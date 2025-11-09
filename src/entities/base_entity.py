"""
base_entity.py
--------------
Defines the BaseEntity class, which serves as the foundational interface
for all active in-game entities (e.g., Player, Enemy, Bullet).

Responsibilities
----------------
- Provide shared attributes such as image, rect, and alive state.
- Define consistent update and draw interfaces for all entities.
- Support both sprite-based and shape-based rendering for flexibility.
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
    def __init__(self, x, y, image=None,
                 *, render_mode=None, shape_type=None,
                 color=None, size=None, shape_kwargs=None):
        """
        Initialize a base entity with its position and visual attributes.

        Args:
            x (float): Initial x-coordinate.
            y (float): Initial y-coordinate.
            image (pygame.Surface | None): Optional surface image used for rendering.
            render_mode (str): "image" for sprite rendering, "shape" for primitive drawing.
            shape_type (str): Shape type when using shape rendering ("rect" or "circle").
            color (tuple[int, int, int]): RGB color for shape rendering.
            size (tuple[int, int]): Size of the shape when not using an image.
            shape_kwargs (dict | None): Optional shape-specific parameters (e.g., width, points).
        """
        # -------------------------------------------------------
        # Core spatial attributes
        # -------------------------------------------------------
        self.image = image
        self.render_mode = render_mode or ("image" if image is not None else "shape")
        self.shape_type = shape_type or "rect"
        self.color = color or (255, 255, 255)
        self.size = size or (32, 32)
        self.shape_kwargs = shape_kwargs or {}

        # Center-aligned rect for consistency
        if self.render_mode == "image" and self.image is not None:
            self.rect = self.image.get_rect(center=(x, y))
        else:
            self.rect = pygame.Rect(0, 0, *self.size)
            self.rect.center = (x, y)

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
        pass

    # ===========================================================
    # Rendering Hook
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render or queue this entity for rendering via the DrawManager.

        Args:
            draw_manager: The DrawManager instance responsible for batching and ordering.
        """
        layer = getattr(self, "layer", Layers.ENEMIES)
        mode = self.render_mode

        # -------------------------------------------------------
        # Case 1: Image rendering (standard sprite)
        # -------------------------------------------------------
        if mode == "image":
            img = self.image
            if img is not None:
                draw_manager.draw_entity(self, layer)
                return

            # Fallback if image missing
            if getattr(DebugLogger, "ENABLED", True):
                DebugLogger.warn(f"{type(self).__name__} missing image; switching to shape")
            self.render_mode = "shape"
            mode = "shape"

        # -------------------------------------------------------
        # Case 2: Shape rendering (primitive)
        # -------------------------------------------------------
        if mode == "shape":
            # Ensure the shape's visual color is always current.
            # If the entity has an image surface (for shape mode), re-fill it.
            if hasattr(self, "image") and self.image:
                self.image.fill(self.color)

            # Queue shape for drawing each frame with the updated color.
            draw_manager.queue_shape(
                self.shape_type,
                self.rect,
                self.color,
                layer,
                **self.shape_kwargs
            )
            return

        # -------------------------------------------------------
        # Case 3: Fallback (no valid data → draw rectangle)
        # -------------------------------------------------------
        if getattr(DebugLogger, "ENABLED", True):
            DebugLogger.warn(f"{type(self).__name__} had no render data; drawing fallback rect")
        draw_manager.queue_shape("rect", self.rect, (255, 255, 255), layer)

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
            f"{type(self).__name__} collided with {type(other).__name__} (no override)"
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
