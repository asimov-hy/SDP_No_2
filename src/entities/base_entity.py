"""
base_entity.py
--------------
Defines the BaseEntity class, which serves as the foundational interface
for all active in-game entities (e.g., Player, Enemy, Bullet).

Coordinate System Standard
--------------------------
All entities in the 202X engine use **center-based coordinates**:
- self.pos represents the entity's visual and physical center.
- self.rect.center is always synchronized with self.pos.
- Movement, rotation, and collisions are performed relative to this center.

Update Pattern
--------------
Subclasses should follow this pattern in their update() method:
    1. Check if alive: if not self.alive: return
    2. Apply movement/logic: self.pos += velocity * dt
    3. Synchronize rect: self.sync_rect()
    4. Update hitbox: if self.hitbox: self.hitbox.update()

Responsibilities
----------------
- Provide shared attributes such as image, rect, and alive state.
- Define consistent update and draw interfaces for all entities.
- Support both sprite-based and shape-based rendering for flexibility.
- Serve as the parent class for specialized gameplay entities.
"""

import pygame
from typing import Optional, Tuple
from src.core.game_settings import Layers
from src.core.utils.debug_logger import DebugLogger


class BaseEntity:
    """
    Common interface for all entities within the game world.

    This class should be subclassed by all game entities (Player, Enemy, Bullet, etc.).

    Subclass Requirements:
    ---------------------
    - Must override update(dt) to implement entity-specific behavior
    - Should call sync_rect() after modifying self.pos
    - Should check self.alive at the start of update()
    - May override on_collision(other) for collision responses
    - Should set appropriate layer in __init__ (e.g., Layers.PLAYER)
    """

    # ===========================================================
    # Class-level defaults (can be overridden by subclasses)
    # ===========================================================
    DEFAULT_SIZE = (32, 32)
    DEFAULT_COLOR = (255, 255, 255)
    DEFAULT_SHAPE_TYPE = "rect"

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(
        self,
        x: float,
        y: float,
        image: Optional[pygame.Surface] = None,
        *,
        render_mode: Optional[str] = None,
        shape_type: Optional[str] = None,
        color: Optional[Tuple[int, int, int]] = None,
        size: Optional[Tuple[int, int]] = None,
        shape_kwargs: Optional[dict] = None
    ):
        """
        Initialize a base entity with its position and visual attributes.

        Args:
            x: Initial x-coordinate (center).
            y: Initial y-coordinate (center).
            image: Optional surface image for sprite rendering.
            render_mode: "image" or "shape". Auto-detected if None.
            shape_type: Shape type for shape rendering ("rect" or "circle").
            color: RGB color tuple for shape rendering.
            size: (width, height) for shape rendering.
            shape_kwargs: Additional shape parameters (e.g., width for outline).

        Notes:
            - If image is provided, render_mode defaults to "image"
            - If image is None, render_mode defaults to "shape"
            - Position (x, y) represents the CENTER of the entity
            - Subclasses should set self.layer appropriately after super().__init__()
        """
        # -------------------------------------------------------
        # Core Spatial Attributes
        # -------------------------------------------------------
        self.pos = pygame.Vector2(x, y)

        # -------------------------------------------------------
        # Rendering Setup
        # -------------------------------------------------------
        self.image = image

        # Auto-detect render mode if not specified
        if render_mode is not None:
            self.render_mode = render_mode
        else:
            self.render_mode = "image" if image is not None else "shape"

        # Shape rendering attributes
        self.shape_type = shape_type or self.DEFAULT_SHAPE_TYPE
        self.color = color or self.DEFAULT_COLOR
        self.size = size or self.DEFAULT_SIZE
        self.shape_kwargs = shape_kwargs or {}

        # -------------------------------------------------------
        # Rect Setup (center-aligned)
        # -------------------------------------------------------
        if self.render_mode == "image" and self.image is not None:
            self.rect = self.image.get_rect(center=(x, y))
        else:
            self.rect = pygame.Rect(0, 0, *self.size)
            self.rect.center = (x, y)

        # -------------------------------------------------------
        # Entity State
        # -------------------------------------------------------
        self.alive = True

        # Default layer - subclasses SHOULD override this
        # (Using ENEMIES as default since most entities in bullet hell are enemies/bullets)
        self.layer = Layers.ENEMIES

        # -------------------------------------------------------
        # Collision Attributes
        # -------------------------------------------------------
        self.collision_tag = "neutral"
        self._hitbox = None
        self.has_hitbox = False  # Legacy flag - kept for compatibility

    # ===========================================================
    # Hitbox Property (cleaner access pattern)
    # ===========================================================
    @property
    def hitbox(self):
        """Get the collision hitbox (may be None if not initialized)."""
        return self._hitbox

    @hitbox.setter
    def hitbox(self, value):
        """
        Set the collision hitbox.

        Typically called by the collision system or in entity __init__.
        Automatically updates has_hitbox flag for compatibility.
        """
        self._hitbox = value
        self.has_hitbox = value is not None

    # ===========================================================
    # Spatial Synchronization
    # ===========================================================
    def sync_rect(self):
        """
        Synchronize rect.center with self.pos.

        IMPORTANT: Subclasses MUST call this after modifying self.pos
        to ensure rendering and collision use the updated position.

        Pattern:
            self.pos += self.velocity * dt  # Move entity
            self.sync_rect()                 # Update rect to match

        Note: This is NOT called automatically in base update() to avoid
        syncing before movement is complete.
        """
        self.rect.center = self.pos

    # ===========================================================
    # Core Update Loop
    # ===========================================================
    def update(self, dt: float):
        """
        Update the entity's state for this frame.

        Base implementation does NOTHING. Subclasses MUST override this
        to implement entity-specific behavior (movement, animation, etc.).

        Recommended pattern for subclasses:
            def update(self, dt):
                if not self.alive:
                    return

                # Apply movement
                self.pos += self.velocity * dt
                self.sync_rect()

                # Update collision
                if self.hitbox:
                    self.hitbox.update()

        Args:
            dt: Time elapsed since last frame (in seconds).
        """
        pass  # Subclasses override this

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Queue this entity for rendering via the DrawManager.

        Handles automatic fallback chain:
            image → shape → debug rect

        If image rendering fails (missing image), automatically falls back
        to shape rendering. If that also fails, draws a debug rect.

        Args:
            draw_manager: The DrawManager instance responsible for rendering.
        """
        layer = self.layer
        mode = self.render_mode

        # -------------------------------------------------------
        # Image Rendering (standard sprite)
        # -------------------------------------------------------
        if mode == "image":
            if self.image is not None:
                draw_manager.draw_entity(self, layer)
                return

            # Fallback: missing image
            DebugLogger.warn(
                f"{type(self).__name__} missing image; switching to shape"
            )
            self.render_mode = "shape"
            mode = "shape"

        # -------------------------------------------------------
        # Shape Rendering (primitive shapes)
        # -------------------------------------------------------
        if mode == "shape":
            # Note: We don't need to fill self.image here!
            # queue_shape() takes self.color directly and uses it each frame.
            # The old self.image.fill() was redundant overhead.

            draw_manager.queue_shape(
                self.shape_type,
                self.rect,
                self.color,
                layer,
                **self.shape_kwargs
            )
            return

        # -------------------------------------------------------
        # Emergency Fallback (should never reach here)
        # -------------------------------------------------------
        DebugLogger.error(
            f"{type(self).__name__} has invalid render_mode='{mode}'; "
            f"drawing debug rect"
        )
        draw_manager.queue_shape("rect", self.rect, (255, 0, 255), layer)

    # ===========================================================
    # Collision Interface
    # ===========================================================
    def on_collision(self, other: "BaseEntity"):
        """
        Handle collision with another entity.

        Base implementation just logs the collision. Subclasses should
        override to implement specific collision responses.

        Called by the collision system when this entity collides with another.

        Common patterns:
            - Check other.collision_tag to determine response
            - Apply damage, destroy bullet, bounce, etc.

        Args:
            other: The entity this one collided with.
        """
        DebugLogger.trace(
            f"{type(self).__name__}[{self.collision_tag}] collided with "
            f"{type(other).__name__}[{other.collision_tag}]"
        )

    def get_hitbox_rect(self) -> Optional[pygame.Rect]:
        """
        Get the collision hitbox rectangle.

        Safe accessor that returns None if hitbox doesn't exist.

        Returns:
            The hitbox rect if available, None otherwise.
        """
        return self._hitbox.rect if self._hitbox else None

    # ===========================================================
    # Utility Methods
    # ===========================================================
    def distance_to(self, other: "BaseEntity") -> float:
        """
        Calculate distance to another entity's center.

        Useful for proximity checks, targeting, etc.

        Args:
            other: The entity to measure distance to.

        Returns:
            Distance in pixels.
        """
        return self.pos.distance_to(other.pos)

    def __repr__(self) -> str:
        """Debug string representation of entity."""
        return (
            f"<{type(self).__name__} "
            f"pos=({self.pos.x:.1f}, {self.pos.y:.1f}) "
            f"tag={self.collision_tag} "
            f"alive={self.alive}>"
        )