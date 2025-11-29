"""
player_core.py
--------------
Defines the minimal Player entity core used to coordinate all components.
"""

import pygame
import os

from src.core.runtime.game_settings import Display, Layers
from src.core.debug.debug_logger import DebugLogger
from src.core.services.config_manager import load_config
from src.core.services.event_manager import get_events, EnemyDiedEvent
from src.core.runtime.session_stats import get_session_stats
from src.core.services.service_locator import ServiceLocator

from src.entities.base_entity import BaseEntity
from src.entities.state_manager import StateManager
from src.entities.entity_state import LifecycleState, InteractionState
from src.entities.entity_types import CollisionTags, EntityCategory
from src.entities.items.shield import Shield
from .player_movement import update_movement
from . import player_ability
from .player_logic import damage_collision
from .player_state import PlayerEffectState


# ===========================================================
# Action Query Wrapper
# ===========================================================
class PlayerInput:
    """Wrapper to simplify action queries without explicit imports."""

    __slots__ = ('input_manager',)

    def __init__(self, input_manager):
        self.input_manager = input_manager

    def pressed(self, action: str) -> bool:
        """Check if action was just pressed."""
        return self.input_manager.action_pressed(action)

    def held(self, action: str) -> bool:
        """Check if action is held."""
        return self.input_manager.action_held(action)

    def released(self, action: str) -> bool:
        """Check if action was just released."""
        return self.input_manager.action_released(action)

    def move(self) -> pygame.Vector2:
        """Get normalized movement vector."""
        return self.input_manager.get_normalized_move()


class Player(BaseEntity):
    """Represents the controllable player entity."""

    def __init__(self, x=None, y=None, image=None,
                 draw_manager=None, input_manager=None):
        """Initialize the player entity."""

        # ========================================
        # 1. Load Config
        # ========================================
        cfg = load_config("player.json", {})
        self.cfg = cfg

        _REQUIRED_SECTIONS = ("core_attributes", "render", "health_states")
        missing = [s for s in _REQUIRED_SECTIONS if s not in cfg]
        if missing:
            DebugLogger.fail(
                f"player.json missing required sections: {missing}",
                category="loading"
            )
            raise ValueError(f"Invalid player.json: missing {missing}")

        core = cfg["core_attributes"]
        render = cfg["render"]
        health_cfg = cfg["health_states"]

        # ========================================
        # 2. Render Setup
        # ========================================
        self.render_mode = render["mode"]
        size = tuple(render["size"])
        default_state = render["default_shape"]

        if self.render_mode == "image":
            if image is None:
                sprite_path = render.get("sprite", {}).get("path")
                scale = (size[0], size[1])  # tuple scale for target dimensions
                # Calculate scale factor from original image size
                if sprite_path and os.path.exists(sprite_path):
                    temp_img = pygame.image.load(sprite_path).convert_alpha()
                    image = pygame.transform.scale(temp_img, size)

                else:
                    DebugLogger.warn(f"Missing sprite: {sprite_path}, using fallback.")
                    image = pygame.Surface(size)
                    image.fill((255, 50, 50))

            shape_data = None
        else:
            image = None
            shape_data = {
                "type": default_state["shape_type"],
                "color": tuple(default_state["color"]),
                "size": size,
                "kwargs": {}
            }

        # Spawn position
        x, y = self._compute_spawn_position(x, y, size, image)

        # ========================================
        # 3. Base Entity Init
        # ========================================
        # Build hitbox config from player config
        hitbox_config = {'scale': core["hitbox_scale"]}

        super().__init__(x, y, image=image, shape_data=shape_data,
                         draw_manager=draw_manager, hitbox_config=hitbox_config)

        if self.render_mode == "shape":
            self.shape_data = shape_data

        # ========================================
        # 4. Core Stats
        # ========================================
        self.velocity = pygame.Vector2(0, 0)
        self.virtual_pos = pygame.Vector2(x, y)
        self.clamped_x = False
        self.clamped_y = False

        self.base_speed = core["speed"]
        self.health = core["health"]
        self.max_health = self.health

        # Player stats - load from progression config
        self.exp = 0
        self.level = 1
        self._exp_table = self._build_exp_table()
        self.exp_required = self._exp_table[self.level]

        self.visible = True
        self.layer = Layers.PLAYER
        self.collision_tag = CollisionTags.PLAYER
        self.category = EntityCategory.PLAYER
        self.state = InteractionState.DEFAULT

        # Stress system
        stress_cfg = cfg.get("stress", {})
        self.stress = 0.0
        self.stress_max = stress_cfg.get("max", 10.0)
        self.stress_threshold = stress_cfg.get("threshold", 8.0)
        self.stress_decay_rate = stress_cfg.get("decay_rate", 4.0)
        self.stress_grace_period = stress_cfg.get("grace_period", 1.0)
        self.stress_per_damage = stress_cfg.get("per_damage", 1.0)
        self._time_since_damage = 0.0

        # 5. Visual State System
        self.health_thresholds = health_cfg["thresholds"]
        self._threshold_moderate = self.health_thresholds["moderate"]
        self._threshold_critical = self.health_thresholds["critical"]

        # Load images if needed
        images = None
        if self.render_mode == "image":
            images = {}
            for state_key, path in health_cfg["image_states"].items():
                # Reuse initial image for normal state if same path
                if state_key == "normal" and path == render.get("sprite", {}).get("path"):
                    images[state_key] = image  # Reuse already loaded
                else:
                    images[state_key] = self._load_and_scale(path, size)

        # Setup via base entity
        self.setup_sprite(
            health=self.health,
            thresholds_dict=self.health_thresholds,
            color_states={k: tuple(v) for k, v in health_cfg["color_states"].items()},
            image_states=images,
            render_mode=self.render_mode
        )

        # ========================================
        # 6. Collision & Combat
        # ========================================

        # Fail immediately if None passed
        if input_manager is None:
            raise ValueError("Player requires input_manager")
        if draw_manager is None:
            raise ValueError("Player requires draw_manager")

        self.input_manager = input_manager
        self.input = PlayerInput(input_manager)

        self._bullet_manager = None
        self._shooting_enabled = False
        combat_cfg = cfg.get("combat", {})
        self.base_shoot_cooldown = combat_cfg.get("shoot_cooldown", 0.5)
        self.bullet_speed = combat_cfg.get("bullet_speed", 900)
        self.damage = combat_cfg.get("collision_damage", 1)
        self.shoot_timer = 0.0

        # ========================================
        # 7. Global Ref & Status
        # ========================================
        self._rotation_enabled = False  # Players don't rotate
        self._death_frames = []  # No death animation frames for player
        self.state_manager = StateManager(self, cfg.get("state_effects", {}))
        self._shield = None

        get_events().subscribe(EnemyDiedEvent, self._on_enemy_died)

        DebugLogger.init_entry("Player Initialized")
        DebugLogger.init_sub(f"Location: ({x:.1f}, {y:.1f})")
        DebugLogger.init_sub(f"Render Mode: {self.render_mode}")

    # ===========================================================
    # Helper Methods
    # ===========================================================
    @staticmethod
    def _compute_spawn_position(x, y, size, image):
        """Compute initial spawn position."""
        if image:
            img_w, img_h = image.get_size()
        else:
            img_w, img_h = size

        if x is None:
            x = Display.WIDTH / 2

        if y is None:
            y = Display.HEIGHT - (img_h / 2) - 10

        return x, y

    @staticmethod
    def _load_and_scale(path, size):
        """Load and scale a single image state."""
        temp_img = pygame.image.load(path).convert_alpha()
        scale = (size[0] / temp_img.get_width(), size[1] / temp_img.get_height())
        return BaseEntity.load_and_scale_image(path, scale)

    @staticmethod
    def _build_exp_table():
        """Build exp lookup table once at init."""
        base = 100
        multiplier = 1.5
        max_level = 200
        max_exp_cap = 999999

        table = [0]
        for lvl in range(1, max_level + 2):
            exp = min(int(base * (multiplier ** (lvl - 1))), max_exp_cap)
            table.append(exp)
        return table

    # ===========================================================
    # Frame Cycle
    # ===========================================================
    def update(self, dt):
        """Update player components."""

        if self.death_state == LifecycleState.DYING:
            if self.anim_manager.update(dt):
                self.mark_dead(immediate=True)
                DebugLogger.state("Player death animation complete", category="player")
            return

        if self.death_state != LifecycleState.ALIVE:
            return

        # Track STUN state before update
        was_stunned = self.state_manager.has_state(PlayerEffectState.STUN)
        in_recovery = self.state_manager.has_state(PlayerEffectState.RECOVERY)

        self.anim_manager.update(dt)
        self.state_manager.update(dt)
        self._update_stress(dt)

        # Detect STUN → RECOVERY transition
        if was_stunned and not self.state_manager.has_state(PlayerEffectState.STUN):
            if self.state_manager.has_state(PlayerEffectState.RECOVERY):
                recovery_cfg = self.state_manager.state_config.get("recovery", {})
                self.anim_manager.play("recovery", duration=recovery_cfg.get("duration", 2.5))
                self._spawn_shield()  # ADD

        # Update shield state
        self._update_shield(dt)  # ADD

        update_movement(self, dt)

        if self._bullet_manager:
            player_ability.update_shooting(self, dt)

    def _spawn_shield(self):
        """Spawn shield entity for RECOVERY state."""
        if self._shield is not None:
            return

        recovery_cfg = self.state_manager.state_config.get("recovery", {})
        radius = recovery_cfg.get("shield_radius", 56)
        knockback = recovery_cfg.get("shield_knockback", 350)

        self._shield = Shield(self, radius=radius, knockback_strength=knockback)

        # Register with collision manager
        collision_mgr = ServiceLocator.get("collision_manager")
        if collision_mgr:
            collision_mgr.register_hitbox(self._shield, shape="circle")

        # Add to spawn_manager for collision detection
        spawn_mgr = ServiceLocator.get("spawn_manager")
        if spawn_mgr:
            spawn_mgr.entities.append(self._shield)

        DebugLogger.state("Shield spawned", category="player")

    def _despawn_shield(self):
        """Remove shield entity."""
        if self._shield is None:
            return

        # Unregister hitbox
        collision_mgr = ServiceLocator.get("collision_manager")
        if collision_mgr:
            collision_mgr.unregister_hitbox(self._shield)

        # Remove from spawn_manager
        spawn_mgr = ServiceLocator.get("spawn_manager")
        if spawn_mgr and self._shield in spawn_mgr.entities:
            spawn_mgr.entities.remove(self._shield)

        self._shield.kill()
        self._shield = None
        DebugLogger.state("Shield despawned", category="player")

    def _update_shield(self, dt):
        """Update shield lifecycle and state."""
        in_recovery = self.state_manager.has_state(PlayerEffectState.RECOVERY)

        if in_recovery and self._shield is not None:
            self._shield.update(dt)

            # Warning blink in last 30% of recovery
            remaining = self.state_manager.get_remaining_time(PlayerEffectState.RECOVERY)
            recovery_cfg = self.state_manager.state_config.get("recovery", {})
            duration = recovery_cfg.get("duration", 2.5)

            if remaining < duration * 0.3:
                self._shield.set_warning_blink(True)
            else:
                self._shield.set_warning_blink(False)

        elif not in_recovery and self._shield is not None:
            self._despawn_shield()

    def _update_stress(self, dt):
        """Decay stress after grace period."""
        self._time_since_damage += dt

        if self._time_since_damage >= self.stress_grace_period and self.stress > 0:
            self.stress = max(0.0, self.stress - self.stress_decay_rate * dt)

    def draw(self, draw_manager):
        """Render player if visible."""
        if not self.visible:
            return

        # Draw shield behind player
        if self._shield is not None:
            self._shield.draw(draw_manager)

        super().draw(draw_manager)

    def on_collision(self, other, collision_tag=None):
        """Handle collision events."""

        tag = collision_tag if collision_tag is not None else getattr(other, "collision_tag", None)
        if tag is None:
            return

        # damaging collisions
        if tag in (CollisionTags.ENEMY, CollisionTags.ENEMY_BULLET):
            damage_collision(self, other)

    # ===========================================================
    # EXP HANDLING
    # ===========================================================
    def _on_enemy_died(self, event):
        """Receive EXP from dead enemies."""
        exp_gain = max(0, event.exp)  # Prevent negative exp
        if exp_gain == 0:
            return

        self.exp += exp_gain

        stats = get_session_stats()
        stats.total_exp_gained += exp_gain

        # Handle multiple level-ups
        while self.exp >= self.exp_required:
            self._level_up()

        DebugLogger.state(
            f"Experience: +{exp_gain} ({self.exp}/{self.exp_required})",
            category="exp"
        )

    def _level_up(self):
        overflow = self.exp - self.exp_required
        self.level += 1
        self.exp_required = self._exp_table[min(self.level, len(self._exp_table) - 1)]
        self.exp = overflow

        stats = get_session_stats()
        stats.max_level_reached = max(stats.max_level_reached, self.level)

        DebugLogger.state(
            f"Level: {self.level}, Next={self.exp_required}",
            category="exp"
        )

    # ===========================================================
    # Stat Properties (with modifiers applied)
    # ===========================================================
    @property
    def speed(self):
        """Get speed with active modifiers applied."""
        return self.state_manager.get_stat("speed", self.base_speed)

    @property
    def shoot_cooldown(self):
        """Get shoot cooldown with fire rate modifiers applied."""
        fire_rate_mult = self.state_manager.get_stat("fire_rate", 1.0)
        return self.base_shoot_cooldown / fire_rate_mult

    @property
    def bullet_manager(self):
        return self._bullet_manager

    @bullet_manager.setter
    def bullet_manager(self, manager):
        """Set manager and synchronize shooting state."""
        self._bullet_manager = manager
        self._shooting_enabled = manager is not None

    def get_bullet_config(self) -> dict:
        """Return bullet configuration for BulletManager registration."""
        render = self.cfg.get("render", {})
        bullet_cfg = render.get("bullet", {})
        combat_cfg = self.cfg.get("combat", {})

        return {
            "path": bullet_cfg.get("path"),
            "size": bullet_cfg.get("size", [16, 32]),
            "damage": combat_cfg.get("bullet_damage", 1),
            "color": (255, 255, 100),  # Fallback color
            "radius": 4
        }
