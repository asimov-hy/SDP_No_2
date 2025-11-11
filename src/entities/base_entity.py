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

Rendering
---------
Image mode (fastest):
    Entity(x, y, image=sprite)

Shape mode (auto-optimized):
    Entity(x, y, shape_data={"type": "circle", "color": (255,0,0), "size": (8,8)}, draw_manager=dm)
    Note: Always pass draw_manager to prebake shapes as images (~4x faster)

Shape fallback (prototyping only):
    Entity(x, y, shape_data={...})  # Slower, renders per-frame

Responsibilities
----------------
- Provide shared attributes such as image, rect, and alive state.
- Define consistent update and draw interfaces for all entities.
- Support both sprite-based and shape-based rendering with auto-optimization.
- Serve as the parent class for specialized gameplay entities.
"""

import pygame
from typing import Optional
from src.core.game_settings import Layers
from src.core.utils.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState, EntityCategory


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
    # Initialization
    # ===========================================================
    def __init__(
        self,
        x: float,
        y: float,
        image: Optional[pygame.Surface] = None,
        shape_data: Optional[dict] = None,
        draw_manager: Optional = None,
    ):
        """
        Initialize entity with flexible rendering options.

        Args:
            x: Initial x-coordinate (center).
            y: Initial y-coordinate (center).
            image: Pre-made sprite surface for image-based rendering.
            shape_data: Shape definition dict for shape-based rendering.
                Format: {
                    "type": str,      # "rect", "circle", "ellipse", etc.
                    "color": tuple,   # RGB tuple (255, 255, 0)
                    "size": tuple,    # (width, height) in pixels
                    "kwargs": dict    # Optional: {"width": 2} for outline, etc.
                }
            draw_manager: DrawManager instance for shape prebaking (optimization).

        Rendering Modes:
            1. Image mode: Provide `image` parameter
            2. Optimized shape: Provide `shape_data` + `draw_manager` (auto-converts to image)
            3. Fallback shape: Provide `shape_data` only (renders per-frame, slower)
            4. Debug default: No params (magenta rect, should not be used in production)

        Performance:
            Always provide draw_manager with shape_data to enable prebaking.
            This gives shape convenience with image performance (~4x faster).

        Examples:
            # Image-based entity (fastest)
            player = Player(100, 100, image=sprite)

            # Shape-based with prebaking (also fast)
            bullet = Bullet(200, 200,
                shape_data={"type": "circle", "color": (255,255,0), "size": (8,8)},
                draw_manager=game.draw_manager
            )

            # Fallback for prototyping (slower)
            test = Entity(50, 50, shape_data={"type": "rect", ...})
        """
        # -------------------------------------------------------
        # Core Spatial Attributes
        # -------------------------------------------------------
        self.pos = pygame.Vector2(x, y)

        # -------------------------------------------------------
        # Rendering Setup (with auto-optimization)
        # -------------------------------------------------------
        # AUTO-OPTIMIZATION: Convert shape to image at creation time
        if image is None and shape_data and draw_manager:
            self.image = draw_manager.prebake_shape(**shape_data)
        else:
            self.image = image

        # -------------------------------------------------------
        # Rect Setup (center-aligned)
        # -------------------------------------------------------
        if self.image:
            self.rect = self.image.get_rect(center=(x, y))
        else:
            # Fallback for entities created without draw_manager
            size = shape_data.get("size", (10, 10)) if shape_data else (10, 10)
            self.rect = pygame.Rect(0, 0, *size)
            self.rect.center = (x, y)
            # Store shape data for manual rendering (fallback path)
            self.shape_data = shape_data

        self.draw_manager = draw_manager

        # -------------------------------------------------------
        # Entity State
        # -------------------------------------------------------
        self.death_state = LifecycleState.ALIVE

        # Default layer - subclasses SHOULD override this
        self.layer = Layers.ENEMIES

        # -------------------------------------------------------
        # Attributes
        # -------------------------------------------------------
        self.category = EntityCategory.EFFECT
        self.collision_tag = "neutral"

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

        Args:
            dt: Time elapsed since last frame (in seconds).
        """
        pass  # Subclasses override this

    def mark_dead(self, immediate=False):
        """
        Mark entity as no longer alive.

        Args:
            immediate: If True, skip DYING phase and go directly to DEAD.
        """
        # Ignore if already fully dead
        if self.death_state == LifecycleState.DEAD:
            return

        if immediate or self.death_state == LifecycleState.DYING:
            # Finalize death immediately
            self.death_state = LifecycleState.DEAD
        else:
            # Begin death sequence (animation, effects, etc.)
            self.death_state = LifecycleState.DYING

        DebugLogger.state(
            f"[{type(self).__name__}] → {self.death_state.name}",
            category="entity"
        )

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Queue this entity for rendering via the DrawManager.

        Rendering priority:
            1. Image (if available) - fastest, uses batched blitting
            2. Shape (if shape_data stored) - fallback, renders per-frame
            3. Debug rect (magenta outline) - emergency fallback

        Performance:
            Path 1 (image) is ~4x faster than path 2 (shape) for large entity counts.
            Always use draw_manager at entity creation to enable automatic prebaking.

        Args:
            draw_manager: The DrawManager instance responsible for rendering.
        """
        if self.image is not None:
            # Fast path: Image-based rendering (batched)
            draw_manager.draw_entity(self, self.layer)
        elif hasattr(self, 'shape_data') and self.shape_data:
            # Fallback path: Shape rendering (per-frame, slower)
            draw_manager.queue_shape(
                self.shape_data["type"],
                self.rect,
                self.shape_data["color"],
                self.layer,
                **self.shape_data.get("kwargs", {})
            )
        else:
            # Emergency fallback: Debug visualization
            DebugLogger.warn(
                f"{type(self).__name__} has no image or shape_data; "
                f"drawing debug rect"
            )
            draw_manager.queue_shape(
                "rect",
                self.rect,
                (255, 0, 255),  # Magenta "something's wrong" indicator
                self.layer,
                width=1
            )

    def refresh_visual(self, new_image=None, new_color=None, shape_type=None, size=None):
        """
        Rebuild entity visuals when appearance changes at runtime.

        Args:
            new_image: Pre-loaded image to use (image mode)
            new_color: RGB tuple to rebake shape with (shape mode)
            shape_type: Shape type if different from current
            size: Size tuple if different from current
        """
        if new_image:
            # Image mode - just swap
            self.image = new_image
        elif new_color and hasattr(self, 'shape_data'):
            if not (hasattr(self, 'draw_manager') and self.draw_manager):
                DebugLogger.warn(f"{type(self).__name__} can't rebake - no draw_manager")
                return

            # Shape mode - rebake
            shape_type = shape_type or self.shape_data.get("type", "rect")
            size = size or self.shape_data.get("size", (10, 10))

            if hasattr(self, 'draw_manager') and self.draw_manager:
                self.image = self.draw_manager.prebake_shape(
                    type=shape_type,
                    size=size,
                    color=new_color
                )

        # Sync rect to new image size while preserving position
        if self.image:
            self.rect = self.image.get_rect(center=self.pos)

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
        pass

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
            f"category={getattr(self, 'category', '?')}>"
        )
