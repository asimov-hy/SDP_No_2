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

from src.core.game_settings import Display, Layers
from src.core.game_state import STATE
from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.systems.combat.collision_hitbox import CollisionHitbox
from .player_config import PLAYER_CONFIG
from .player_state import InteractionState

class Player(BaseEntity):
    """Represents the controllable player entity."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x: float | None = None, y: float | None = None, image: pygame.Surface | None = None):
        """
        Initialize the player entity, load configuration, and prepare rendering and collision systems.

        Args:
            x (float | None): Optional x-coordinate for player spawn position.
            y (float | None): Optional y-coordinate for player spawn position.
            image (pygame.Surface | None): Optional preloaded player image surface.
        """
        cfg = PLAYER_CONFIG
        core = cfg["core_attributes"]
        default_state = cfg["default_shape"]

        # -------------------------------------------------------
        # 1) Visual setup (image or shape)
        # -------------------------------------------------------
        sprite_cfg = cfg["sprite"]
        size = cfg["size"]

        self.render_mode = cfg["render_mode"]

        image = self._load_sprite(cfg, image)
        image = self._apply_scaling(size, image)

        # Compute spawn position
        x, y = self._compute_spawn_position(x, y, image)

        # -------------------------------------------------------
        # 2) BaseEntity initialization
        # -------------------------------------------------------
        super().__init__(
            x, y,
            image=image,
            render_mode=self.render_mode,
            shape_type=default_state["shape_type"],
            color=default_state["color"],
            size=cfg["size"],
        )

        # -------------------------------------------------------
        # 3) Core attributes
        # -------------------------------------------------------
        self.velocity = pygame.Vector2(0, 0)
        self.speed = core["speed"]
        self.health = core["health"]
        self.max_health = self.health
        self.layer = Layers.PLAYER
        self.alive = True
        self.visible = True

        # -------------------------------------------------------
        # 4) Interaction state management (Enum-based)
        # -------------------------------------------------------
        self.state = InteractionState.DEFAULT

        # -------------------------------------------------------
        # 5) Health-based visuals
        # -------------------------------------------------------
        self.image_states = cfg["image_states"]
        self.color_states = cfg["color_states"]
        self.health_thresholds = cfg["health_thresholds"]

        # Defer visual update to logic layer
        try:
            from .player_logic import update_visual_state
            update_visual_state(self)
        except ImportError:
            DebugLogger.warn("player_logic not loaded yet — skipping visual update")

        # -------------------------------------------------------
        # 6) Collision setup
        # -------------------------------------------------------
        self.collision_tag = "player"
        self.hitbox_scale = core["hitbox_scale"]
        self.hitbox: CollisionHitbox | None = CollisionHitbox(self, self.hitbox_scale)
        self.has_hitbox = True

        # -------------------------------------------------------
        # 7) Combat setup
        # -------------------------------------------------------
        self.bullet_manager = None
        self.shoot_cooldown = 0.1
        self.shoot_timer = 0.0

        # -------------------------------------------------------
        # 8) Animation manager setup
        # -------------------------------------------------------
        from src.graphics.animation_manager import AnimationManager

        self.animation_manager = AnimationManager(self)
        DebugLogger.state("AnimationManager initialized and linked to Player", category="animation")

        STATE.player_ref = self

        DebugLogger.init(
            f"Initialized Player at ({x:.1f}, {y:.1f}) | Speed={self.speed} | HP={self.health}"
        )

    # ===========================================================
    # Helper Methods
    # ===========================================================
    @staticmethod
    def _load_sprite(cfg, image):
        """Load player sprite from disk or create a fallback if missing."""
        if image:
            return image

        # Use nested config path
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
        """Scale sprite according to configuration."""
        if not image:
            return image
        image = pygame.transform.scale(image, size)
        return image

    @staticmethod
    def _compute_spawn_position(x, y, image):
        """Compute initial spawn position relative to screen and sprite size."""
        img_w, img_h = image.get_size() if image else (64, 64)

        # Center horizontally
        if x is None:
            x = Display.WIDTH / 2

        # Place player near bottom, keeping full sprite visible
        if y is None:
            y = Display.HEIGHT - (img_h / 2) - 10

        DebugLogger.state(f"Spawn position set to ({x:.1f}, {y:.1f})")
        return x, y

    # ===========================================================
    # Frame Cycle
    # ===========================================================
    def update(self, dt):
        """
        Update player state each frame by delegating to subsystems.

        Args:
            dt (float): Delta time since last frame in seconds.
        """
        if not self.alive:
            return

        from .player_movement import update_movement
        from .player_combat import update_shooting

        # Movement and combat updates
        move_vec = getattr(self, "move_vec", pygame.Vector2(0, 0))
        update_movement(self, dt, move_vec)
        update_shooting(self, dt)

        # Collision update
        if self.hitbox:
            self.hitbox.update()

        if getattr(self, "animation_manager", None):
            self.animation_manager.update(dt)

    def draw(self, draw_manager):
        """
        Render the player entity depending on mode and visibility.

        Args:
            draw_manager (DrawManager): The central draw manager used for queued rendering.
        """
        if not self.visible:
            return
        super().draw(draw_manager)

    def on_collision(self, other):
        """
        Delegate collision handling to the combat subsystem.

        Args:
            other (BaseEntity): The entity collided with.
        """
        tag = getattr(other, "collision_tag", None)

        if tag is None:
            DebugLogger.warn("Collision occurred with untagged entity.")
            return

        # Combat-related collisions
        if tag in ("enemy", "enemy_bullet"):
            from .player_combat import damage_collision
            damage_collision(self, other)
            return