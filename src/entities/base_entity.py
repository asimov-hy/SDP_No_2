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
from src.core.settings import Debug, Layers
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
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))
        self.alive = True

        if Debug.VERBOSE_ENTITY_INIT:
            DebugLogger.init(f"Entity initialized at ({x}, {y})")

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
