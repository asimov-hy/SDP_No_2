"""
player_base.py
--------------
Defines the Player entity and coordinates its movement, combat, and visual state.

Responsibilities
----------------
- Initialize the player sprite, hitbox, and configuration.
- Delegate per-frame logic to modular subsystems:
    - Movement → player_movement.py
    - Combat   → player_combat.py
- Maintain player-specific attributes such as health, invulnerability, and visibility.
"""

import os
import pygame
from src.core.game_settings import Display, Layers
from src.core.game_state import STATE
from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.systems.combat.collision_hitbox import CollisionHitbox
from .player_config import PLAYER_CONFIG


class Player(BaseEntity):
    """Represents the controllable player entity."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x=None, y=None, image=None):
        """
        Initialize the player entity, load configuration,
        and prepare rendering and collision systems.
        """
        cfg = PLAYER_CONFIG

        # -------------------------------------------------------
        # 1) Sprite setup
        # -------------------------------------------------------
        if cfg["render_mode"] == "image":
            image = self._load_sprite(cfg, image)
            image = self._apply_scaling(cfg, image)

        # -------------------------------------------------------
        # 2) Spawn position
        # -------------------------------------------------------
        x, y = self._compute_spawn_position(x, y, image)

        # -------------------------------------------------------
        # 3) BaseEntity initialization
        # -------------------------------------------------------
        super().__init__(
            x, y,
            image=image,
            render_mode=cfg["render_mode"],
            shape_type=cfg["shape_type"],
            color=cfg["color"],
            size=cfg["size"],
        )

        # -------------------------------------------------------
        # 4) Core attributes
        # -------------------------------------------------------
        self.velocity = pygame.Vector2(0, 0)
        self.speed = cfg["speed"]
        self.health = cfg["health"]
        self.invincible = cfg["invincible"]
        self.layer = Layers.PLAYER
        STATE.player_ref = self

        # -------------------------------------------------------
        # 5) Blinking / invulnerability
        # -------------------------------------------------------
        self.blinking = False
        self.blink_timer = 0.0
        self.blink_duration = 1.5
        self.blink_interval = 0.1
        self.visible = True

        # -------------------------------------------------------
        # 6) Collision setup
        # -------------------------------------------------------
        self.collision_tag = "player"
        self.hitbox_scale = cfg["hitbox_scale"]
        self.hitbox = CollisionHitbox(self, self.hitbox_scale)
        self.has_hitbox = True

        # -------------------------------------------------------
        # 7) Combat setup
        # -------------------------------------------------------
        self.bullet_manager = None
        self.shoot_cooldown = 0.1
        self.shoot_timer = 0.0

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
        path = cfg.get("sprite_path")
        if not path or not os.path.exists(path):
            DebugLogger.warn(f"[Player] Missing sprite: {path}, using fallback.")
            placeholder = pygame.Surface((64, 64))
            placeholder.fill((255, 50, 50))
            return placeholder
        image = pygame.image.load(path).convert_alpha()
        DebugLogger.state(f"Loaded sprite from {path}")
        return image

    @staticmethod
    def _apply_scaling(cfg, image):
        """Scale sprite according to configuration."""
        if not image or cfg["scale"] == 1.0:
            return image
        w, h = image.get_size()
        new_size = (int(w * cfg["scale"]), int(h * cfg["scale"]))
        image = pygame.transform.scale(image, new_size)
        DebugLogger.state(f"Sprite scaled to {new_size}")
        return image

    @staticmethod
    def _compute_spawn_position(x, y, image):
        """Compute initial spawn position relative to screen and sprite size."""
        img_w, img_h = image.get_size() if image else (64, 64)
        if x is None:
            x = (Display.WIDTH / 2) - (img_w / 2)
        if y is None:
            y = Display.HEIGHT - img_h - 10
        DebugLogger.state(f"Spawn position set to ({x:.1f}, {y:.1f})")
        return x, y

    # ===========================================================
    # Frame Update
    # ===========================================================
    def update(self, dt):
        """Update player state each frame by delegating to movement and combat modules."""
        if not self.alive:
            return

        from .player_movement import update_movement
        from .player_combat import update_shooting, update_blinking

        move_vec = getattr(self, "move_vec", pygame.Vector2(0, 0))
        update_movement(self, dt, move_vec)
        update_shooting(self, dt)
        update_blinking(self, dt)

        if self.hitbox:
            self.hitbox.update()

    def on_collision(self, other):
        """Delegate collision handling to combat logic."""
        from .player_combat import on_collision
        on_collision(self, other)

    def draw(self, draw_manager):
        """Render the player if visible (respects blinking/invulnerability state)."""
        if not self.visible:
            return
        super().draw(draw_manager)
