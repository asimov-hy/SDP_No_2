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

from src.entities.base_entity import BaseEntity
from src.entities.state_manager import StateManager
from src.entities.entity_state import LifecycleState, InteractionState
from src.entities.entity_types import CollisionTags, EntityCategory
from .player_movement import update_movement
from . import player_ability
from .player_logic import damage_collision


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

        if "core_attributes" not in cfg or "render" not in cfg or "health_states" not in cfg:
            raise ValueError("Invalid player.json: missing required sections")

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
                    scale = (size[0] / temp_img.get_width(), size[1] / temp_img.get_height())
                    image = BaseEntity.load_and_scale_image(sprite_path, scale)

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
        self.base_speed = core["speed"]
        self.health = core["health"]
        self.max_health = self.health

        # Player stats
        self.exp = 0
        self.level = 1
        self.exp_required = 30

        self.visible = True
        self.layer = Layers.PLAYER
        self.collision_tag = CollisionTags.PLAYER
        self.category = EntityCategory.PLAYER
        self.state = InteractionState.DEFAULT

        # ========================================
        # 5. Visual State System
        # ========================================
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
        self.base_shoot_cooldown = 0.1
        self.shoot_timer = 0.0

        # ========================================
        # Load Player Bullet Sprite
        # ========================================
        bullet_path = "assets/images/sprites/projectiles/100H.png"
        temp_img = pygame.image.load(bullet_path).convert_alpha() if os.path.exists(bullet_path) else None
        if temp_img:
            scale = (16 / temp_img.get_width(), 32 / temp_img.get_height())
            self.bullet_image = BaseEntity.load_and_scale_image(bullet_path, scale)
        else:
            DebugLogger.warn(f"Missing bullet sprite: {bullet_path}")
            self.bullet_image = pygame.Surface((8, 16), pygame.SRCALPHA)
            pygame.draw.rect(self.bullet_image, (255, 255, 100), (0, 0, 8, 16))

        # ========================================
        # 7. Global Ref & Status
        # ========================================
        self._rotation_enabled = False  # Players don't rotate
        self._death_frames = []  # No death animation frames for player
        self.state_manager = StateManager(self, cfg.get("state_effects", {}))

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

    # ===========================================================
    # Frame Cycle
    # ===========================================================
    def update(self, dt):
        """Update player components."""

        if self.death_state == LifecycleState.DYING:
            # Update animation; returns True when finished
            if self.anim_manager.update(dt):
                # Finalize death
                self.mark_dead(immediate=True)
                DebugLogger.state("Player death animation complete", category="player")
            return

        if self.death_state != LifecycleState.ALIVE:
            return

        self.anim_manager.update(dt)
        self.state_manager.update(dt)

        # self.input_manager.update()
        update_movement(self, dt)

        # 4. Ability logic
        if self._bullet_manager:
            player_ability.update_shooting(self, dt)

    def draw(self, draw_manager):
        """Render player if visible."""
        if not self.visible:
            return
        super().draw(draw_manager)

    def on_collision(self, other):
        """Handle collision events."""

        tag = getattr(other, "collision_tag", None)
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
        self.exp += event.exp

        DebugLogger.state(
            f"Experience: {event.exp} ({self.exp}/{self.exp_required})",
            category="exp"
        )

        if self.exp >= self.exp_required:
            self._level_up()

    def _level_up(self):
        self.level += 1
        self.exp = 0

        # Smooth EXP curve
        self.exp_required = int(30 * (1.15 ** (self.level - 1)))

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
