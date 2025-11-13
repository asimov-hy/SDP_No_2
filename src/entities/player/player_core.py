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
        """
        Initialize the player entity.

        Args:
            x: Optional x-coordinate for player spawn position.
            y: Optional y-coordinate for player spawn position.
            image: Optional preloaded player image surface.
            draw_manager: Required for shape-based rendering optimization.
        """
        cfg = load_config("player_config.json", {})
        self.cfg = cfg

        core = cfg["core_attributes"]
        render = cfg["render"]
        health = cfg["health_states"]

        self.render_mode = render["mode"]
        size = tuple(render["size"])
        default_state = render["default_shape"]

        # --- Visual setup ---
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

        # --- Spawn position ---
        x, y = self._compute_spawn_position(x, y, size, image)

        # --- Base entity init ---
        super().__init__(x, y, image=image, shape_data=shape_data, draw_manager=draw_manager)

        if self.render_mode == "shape":
            self.shape_data = shape_data

        # --- Core stats ---
        self.velocity = pygame.Vector2(0, 0)
        self.speed = core["speed"]
        self.health = core["health"]
        self.max_health = self.health
        self.visible = True
        self.layer = Layers.PLAYER
        self.collision_tag = CollisionTags.PLAYER
        self.category = EntityCategory.PLAYER

        # --- Interaction state ---
        self.state = InteractionState.DEFAULT

        # --- Visual states ---
        self.image_states = health["image_states"]
        self.color_states = health["color_states"]
        self.health_thresholds = health["thresholds"]
        self._threshold_moderate = self.health_thresholds["moderate"]
        self._threshold_critical = self.health_thresholds["critical"]
        self._color_cache = self.color_states

        if self.render_mode == "image":
            self._image_cache = {
                "normal": self._load_and_scale(self.image_states["normal"], size),
                "damaged_moderate": self._load_and_scale(self.image_states["damaged_moderate"], size),
                "damaged_critical": self._load_and_scale(self.image_states["damaged_critical"], size)
            }
        else:
            self._image_cache = {}

        # Track health for dirty checking
        self._cached_health = self.health

        # --- Collision setup ---
        self.hitbox_scale = core["hitbox_scale"]

        # --- Combat setup ---
        if input_manager is not None:
            self.input_manager = input_manager
        self.bullet_manager = None
        self.shoot_cooldown = 0.1
        self.shoot_timer = 0.0

        # --- Animation manager --- WIP
        # from src.graphics.animation_manager import AnimationManager
        # self.animation_manager = AnimationManager(self)

        # --- Global reference ---
        STATE.player_ref = self
        self.status_manager = StatusManager(self, cfg["status_effects"])

        DebugLogger.init_entry("Player Initialized")
        DebugLogger.init_sub(f"Player Location: ({x:.1f}, {y:.1f})")
        DebugLogger.init_sub(f"Render Mode: {self.render_mode}")
        DebugLogger.init_sub(f"Speed: {self.speed}")
        DebugLogger.init_sub(f"Health: {self.health}")

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
        if self.death_state != LifecycleState.ALIVE:
            return

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

        if tag in (CollisionTags.ENEMY, CollisionTags.ENEMY_BULLET):
            from .player_ability import damage_collision
            damage_collision(self, other)
