"""
base_entity.py
--------------
Defines the BaseEntity class, which serves as the foundational interface
for all active in-game entities (e.g., Player, Enemy, Bullet).

Responsibilities
----------------
- Provide shared attributes such as image, rect, and alive state.
- Define consistent update and draw interfaces for all entities.
- Serve as the parent class for specialized gameplay entities.
"""

import pygame
from src.core.game_settings import Layers
from src.core.utils.debug_logger import DebugLogger


class BaseEntity:
    """Common interface for all entities within the game world."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image):
        """
        Initialize a base entity with its position and sprite.

        Args:
            x (float): Initial x-coordinate.
            y (float): Initial y-coordinate.
            image (pygame.Surface): Surface image used for rendering.
        """
        # -------------------------------------------------------
        # Core spatial attributes
        # -------------------------------------------------------
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.Vector2(x, y)

        # -------------------------------------------------------
        # Entity state
        # -------------------------------------------------------
        self.alive = True
        self.layer = Layers.ENEMIES

        # -------------------------------------------------------
        # Collision attributes
        # -------------------------------------------------------
        self.hitbox = None
        self.has_hitbox = False
        self.collision_tag = "neutral"

        # DebugLogger.init(f" {type(self).__name__} initialized at ({x:.1f}, {y:.1f})")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Update the entity's state. Should be overridden by subclasses.

        Args:
            dt (float): Time elapsed since the last frame (in seconds).
        """
        # Base class provides no movement or logic.
        # Subclasses such as Player, Enemy, or Bullet implement behavior here.
        DebugLogger.trace(f"Update called (dt={dt:.4f})")

    # ===========================================================
    # Rendering Hook
    # ===========================================================
    def draw(self, draw_manager):
        """
        Queue this entity for rendering via the DrawManager.

        Args:
            draw_manager: The DrawManager instance responsible for batching.
        """
        draw_manager.draw_entity(self, layer=getattr(self, 'layer', Layers.ENEMIES))

    # ===========================================================
    # Collision Handling
    # ===========================================================
    def on_collision(self, other):
        """
        Handle collision with another entity.
        Should be overridden by subclasses to define specific behavior.

        Args:
            other (BaseEntity): The other entity involved in the collision.
        """
        DebugLogger.trace(
            f"[CollisionIgnored] {type(self).__name__} collided with {type(other).__name__} (no override)"
        )

    # ===========================================================
    # Hitbox Accessor
    # ===========================================================
    def get_hitbox_rect(self):
        """
        Safely return the current hitbox rect for this entity.

        Returns:
            pygame.Rect | None: The hitbox rect if available.
        """
        return self.hitbox.rect if getattr(self, "hitbox", None) else None

