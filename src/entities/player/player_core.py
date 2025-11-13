"""
player_core.py
--------------
Defines the minimal Player entity core used to coordinate all components.

Responsibilities
----------------
- Initialize player sprite, hitbox, and configuration
- Manage base attributes (position, speed, health placeholder)
- Delegate updates to:
    - Movement → player_movement.py
    - Combat   → player_ability.py
    - Logic    → player_logic.py (status_effects, animation_effects, visuals)
"""

import pygame
import os

from src.core.runtime.game_settings import Display, Layers
from src.core.runtime.game_state import STATE
from src.core.debug.debug_logger import DebugLogger
from src.core.services.config_manager import load_config

from src.entities.base_entity import BaseEntity
from src.entities.status_manager import StatusManager
from src.entities.entity_state import CollisionTags, LifecycleState, EntityCategory

from .player_state import InteractionState


class Player(BaseEntity):
    """Represents the controllable player entity."""

    def __init__(self, x: float | None = None, y: float | None = None,
                 image: pygame.Surface | None = None, draw_manager=None,
                 input_manager=None):
        """Initialize the player entity."""

        # ========================================
        # 1. Load Config
        # ========================================
        cfg = load_config("player_config.json", {})
        self.cfg = cfg

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
            image = self._load_sprite(render, image)
            image = self._apply_scaling(size, image)
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
        super().__init__(x, y, image=image, shape_data=shape_data, draw_manager=draw_manager)

        if self.render_mode == "shape":
            self.shape_data = shape_data

        # ========================================
        # 4. Core Stats
        # ========================================
        self.velocity = pygame.Vector2(0, 0)
        self.speed = core["speed"]
        self.health = core["health"]
        self.max_health = self.health
        self._cached_health = self.health

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
            images = {
                state_key: self._load_and_scale(path, size)
                for state_key, path in health_cfg["image_states"].items()
            }

        # Setup via base entity
        self.setup_visual_states(
            health=self.health,
            thresholds_dict=self.health_thresholds,
            color_states={k: tuple(v) for k, v in health_cfg["color_states"].items()},
            image_states=images,
            render_mode=self.render_mode
        )

        # ========================================
        # 6. Collision & Combat
        # ========================================
        self.hitbox_scale = core["hitbox_scale"]

        if input_manager is not None:
            self.input_manager = input_manager
        self.bullet_manager = None
        self.shoot_cooldown = 0.1
        self.shoot_timer = 0.0

        # ========================================
        # 7. Global Ref & Status
        # ========================================
        STATE.player_ref = self
        self.status_manager = StatusManager(self, cfg["status_effects"])

        DebugLogger.init_entry("Player Initialized")
        DebugLogger.init_sub(f"Location: ({x:.1f}, {y:.1f})")
        DebugLogger.init_sub(f"Render Mode: {self.render_mode}")

    # ===========================================================
    # Helper Methods
    # ===========================================================
    @staticmethod
    def _load_sprite(render_cfg, image):
        """Load player sprite from disk or fallback."""
        if image:
            return image

        sprite_path = render_cfg.get("sprite", {}).get("path")

        if not sprite_path or not os.path.exists(sprite_path):
            DebugLogger.warn(f"Missing sprite: {sprite_path}, using fallback.")
            placeholder = pygame.Surface((64, 64))
            placeholder.fill((255, 50, 50))
            return placeholder

        image = pygame.image.load(sprite_path).convert_alpha()
        DebugLogger.state(f"Loaded sprite from {sprite_path}")
        return image

    @staticmethod
    def _apply_scaling(size, image):
        """Scale sprite to configured size."""
        if not image:
            return image
        return pygame.transform.scale(image, size)

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
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, size)

    # ===========================================================
    # Frame Cycle
    # ===========================================================
    def update(self, dt):
        """Update player components."""

        if self.death_state == LifecycleState.DYING:
            # Update animation; returns True when finished
            if self.anim.update(self, dt):
                # Finalize death
                self.mark_dead(immediate=True)
                DebugLogger.state("Player death animation complete", category="player")
            return

        if self.death_state != LifecycleState.ALIVE:
            return

        self.anim.update(self, dt)

        # 1. Time-based status_effects and temporary states
        self.status_manager.update(dt)
        # 2. Input collection
        self.input_manager.update()

        # 3. Movement and physics
        from .player_movement import update_movement
        move_vec = getattr(self, "move_vec", pygame.Vector2(0, 0))
        update_movement(self, dt, move_vec)

        # 4. Combat logic
        from .player_ability import update_shooting
        attack_held = self.input_manager.is_attack_held()
        update_shooting(self, dt, attack_held)

        # if self.animation_manager:
        #     self.animation_manager.update(dt)


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
            from .player_logic import damage_collision
            damage_collision(self, other)
