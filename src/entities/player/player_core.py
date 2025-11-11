"""
player_core.py
--------------
Defines the minimal Player entity core used to coordinate all subsystems.

Responsibilities
----------------
- Initialize player sprite, hitbox, and configuration
- Manage base attributes (position, speed, health placeholder)
- Delegate updates to:
    - Movement → player_movement.py
    - Combat   → player_combat.py
    - Logic    → player_logic.py (state, effects, visuals)
"""

import pygame
import os

from src.core.engine.input_manager import InputManager
from src.core.game_settings import Display, Layers
from src.core.game_state import STATE
from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import CollisionTags
from src.systems.combat.collision_hitbox import CollisionHitbox
from .player_config import PLAYER_CONFIG
from .player_state import InteractionState



class Player(BaseEntity):
    """Represents the controllable player entity."""

    def __init__(self, x: float | None = None, y: float | None = None,
                 image: pygame.Surface | None = None, draw_manager=None):
        """
        Initialize the player entity.

        Args:
            x: Optional x-coordinate for player spawn position.
            y: Optional y-coordinate for player spawn position.
            image: Optional preloaded player image surface.
            draw_manager: Required for shape-based rendering optimization.
        """
        cfg = PLAYER_CONFIG
        self.cfg = cfg
        core = cfg["core_attributes"]
        default_state = cfg["default_shape"]

        self.render_mode = cfg["render_mode"]
        size = tuple(cfg["size"])

        # -------------------------------------------------------
        # 1) Load/prepare visual asset
        # -------------------------------------------------------
        if self.render_mode == "image":
            image = self._load_sprite(cfg, image)
            image = self._apply_scaling(size, image)
            shape_data = None
        else:  # shape mode
            image = None
            shape_data = {
                "type": default_state["shape_type"],
                "color": tuple(default_state["color"]),
                "size": size,
                "kwargs": {}
            }

        # -------------------------------------------------------
        # 2) Compute spawn position
        # -------------------------------------------------------
        x, y = self._compute_spawn_position(x, y, size, image)

        # -------------------------------------------------------
        # 3) BaseEntity initialization (FIXED API)
        # -------------------------------------------------------
        super().__init__(
            x, y,
            image=image,
            shape_data=shape_data,
            draw_manager=draw_manager  # Pass through for prebaking
        )

        # -------------------------------------------------------
        # 4) Core attributes
        # -------------------------------------------------------
        self.velocity = pygame.Vector2(0, 0)
        self.speed = core["speed"]
        self.health = core["health"]
        self.max_health = self.health
        self.layer = Layers.PLAYER
        self.collision_tag = CollisionTags.PLAYER
        self.alive = True
        self.visible = True

        # -------------------------------------------------------
        # 5) Interaction state
        # -------------------------------------------------------
        self.state = InteractionState.DEFAULT

        # -------------------------------------------------------
        # 6) Visual state config (for dynamic damage visuals)
        # -------------------------------------------------------
        self.image_states = cfg["image_states"]
        self.color_states = cfg["color_states"]
        self.health_thresholds = cfg["health_thresholds"]

        # Cache thresholds as attributes (avoid dict lookup)
        self._threshold_moderate = self.health_thresholds["moderate"]
        self._threshold_critical = self.health_thresholds["critical"]

        # Cache visual states
        self._color_cache = self.color_states  # Already a dict
        if self.render_mode == "image":
            # Preload ALL image states at init
            self._image_cache = {
                "normal": self._load_and_scale(self.image_states["normal"]),
                "damaged_moderate": self._load_and_scale(self.image_states["damaged_moderate"]),
                "damaged_critical": self._load_and_scale(self.image_states["damaged_critical"])
            }
        else:
            self._image_cache = {}

        # Track health for dirty checking
        self._cached_health = self.health

        # Defer visual update to logic layer
        try:
            from .player_logic import update_visual_state
            update_visual_state(self)
        except ImportError:
            DebugLogger.warn("player_logic not loaded yet — skipping visual update")

        # -------------------------------------------------------
        # 7) Collision setup
        # -------------------------------------------------------
        self.hitbox_scale = core["hitbox_scale"]

        # -------------------------------------------------------
        # 8) Combat setup
        # -------------------------------------------------------
        self.input_manager = InputManager()
        self.bullet_manager = None
        self.shoot_cooldown = 0.1
        self.shoot_timer = 0.0

        # -------------------------------------------------------
        # 9) Animation manager
        # -------------------------------------------------------
        from src.graphics.animation_manager import AnimationManager
        self.animation_manager = AnimationManager(self)

        STATE.player_ref = self

        DebugLogger.init(
            f"Player @ ({x:.1f}, {y:.1f}) | Mode={self.render_mode} | "
            f"Speed={self.speed} | HP={self.health}"
        )

    # ===========================================================
    # Helper Methods
    # ===========================================================
    @staticmethod
    def _load_sprite(cfg, image):
        """Load player sprite from disk or fallback."""
        if image:
            return image

        sprite_cfg = cfg.get("sprite", {})
        path = sprite_cfg.get("path")
        if not path or not os.path.exists(path):
            DebugLogger.warn(f"Missing sprite: {path}, using fallback.")
            placeholder = pygame.Surface((64, 64))
            placeholder.fill((255, 50, 50))
            return placeholder

        image = pygame.image.load(path).convert_alpha()
        DebugLogger.state(f"Loaded sprite from {path}")
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
    def _load_and_scale(self, path):
        """Load and scale a single image state."""
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(img, tuple(self.size))

    # ===========================================================
    # Frame Cycle
    # ===========================================================
    def update(self, dt):
        """Update player subsystems."""
        if not self.alive:
            return

        self.input_manager.update()

        from .player_movement import update_movement
        from .player_combat import update_shooting

        move_vec = getattr(self, "move_vec", pygame.Vector2(0, 0))
        update_movement(self, dt, move_vec)
        attack_held = self.input_manager.is_attack_held()
        update_shooting(self, dt, attack_held)

        if self.animation_manager:
            self.animation_manager.update(dt)

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
            from .player_combat import damage_collision
            damage_collision(self, other)
