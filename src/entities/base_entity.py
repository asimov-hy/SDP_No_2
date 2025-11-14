"""
base_entity.py
--------------
Defines the BaseEntity class, which serves as the foundational interface
for all active in-game entities_animation (e.g., Player, Enemy, Bullet).

Coordinate System Standard
--------------------------
All entities_animation in the 202X runtime use **center-based coordinates**:
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
- Define consistent update and draw interfaces for all entities_animation.
- Support both sprite-based and shape-based rendering with auto-optimization.
- Serve as the parent class for specialized gameplay entities_animation.
"""

import pygame
from typing import Optional
from src.core.runtime.game_settings import Layers, Bounds, Display
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState, EntityCategory
from src.graphics.animations.animation_controller import AnimationController


class BaseEntity:
    """
    Common interface for all entities_animation within the game level.

    This class should be subclassed by all game entities_animation (Player, Enemy, Bullet, etc.).

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
        # Validation: Prevent API misuse
        # -------------------------------------------------------
        if image is not None and shape_data is not None:
            raise ValueError(
                f"{type(self).__name__}: Cannot provide both 'image' AND 'shape_data'. "
                f"Use one or the other."
            )

        if shape_data and not draw_manager:
            DebugLogger.warn(
                f"{type(self).__name__}: shape_data provided without draw_manager. "
                f"Shape will render per-frame (slow). Pass draw_manager for optimization."
            )

        # AUTO-OPTIMIZATION: Convert shape to image at creation time
        if image is None and shape_data and draw_manager:
            kwargs = shape_data.get("kwargs", {})
            kwargs = kwargs.copy()
            self.image = draw_manager.prebake_shape(
                type=shape_data["type"],
                size=shape_data["size"],
                color=shape_data["color"],
                **kwargs
            )

            sd_copy = shape_data.copy()
            if "kwargs" in shape_data:
                sd_copy["kwargs"] = shape_data["kwargs"].copy()
            self.shape_data = sd_copy
        else:
            self.image = image

        # Store base image for rotation (if image was created)
        if self.image:
            self._base_image = self.image

        # -------------------------------------------------------
        # Rect Setup (center-aligned)
        # -------------------------------------------------------
        if self.image:
            self.rect = self.image.get_rect(center=(x, y))
        else:
            # Fallback for entities_animation created without draw_manager
            size = shape_data.get("size", (10, 10)) if shape_data else (10, 10)
            self.rect = pygame.Rect(0, 0, *size)
            self.rect.center = (x, y)
            # Store shape config for manual rendering (fallback path)
            self.shape_data = shape_data

        self.draw_manager = draw_manager

        # Rotation Support (optional, used by entities that rotate)
        self._base_image = None  # Unrotated base image (set after image creation)
        self.rotation_angle = 0  # Current rotation in degrees
        self._rotation_enabled = False

        # Entity State
        self.death_state = LifecycleState.ALIVE

        # Default layer - subclasses SHOULD override this
        self.layer = Layers.ENEMIES

        # -------------------------------------------------------
        # Attributes
        # -------------------------------------------------------
        self.category = EntityCategory.EFFECT
        self.collision_tag = "neutral"
        self.tags = set()

        self._current_sprite = None  # Subclasses set initial state
        self._sprite_config = {}  # Subclasses populate state→image/color mapping

        self.anim = AnimationController()

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
            # Begin death sequence (animation, animation_effects, etc.)
            self.death_state = LifecycleState.DYING

        DebugLogger.state(
            f"[{type(self).__name__}] → {self.death_state.name}",
            category="entity"
        )

    def reset(self, x, y, **kwargs):
        """
        Reset entity to reusable state (for pooling).
        Subclasses override to reset specific attributes.
        """
        self.pos.update(x, y)
        self.death_state = LifecycleState.ALIVE
        self.sync_rect()

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

    def refresh_sprite(self, new_image=None, new_color=None, shape_type=None, size=None):
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

        # Update base image for rotation support
        if self.image:
            self._base_image = self.image
            self.rotation_angle = 0  # Reset rotation

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

    # ===========================================================
    # Bounds & Margin System
    # ===========================================================
    def get_cleanup_margin(self):
        """
        Returns cleanup margin based on entity category.
        Entity is removed when this far offscreen.
        """
        margin_map = {
            EntityCategory.ENEMY: Bounds.ENEMY_CLEANUP_MARGIN,
            EntityCategory.PROJECTILE: Bounds.BULLET_ENEMY_MARGIN,  # Default for bullets
            EntityCategory.PICKUP: Bounds.ITEM_CLEANUP_MARGIN,
            EntityCategory.ENVIRONMENT: Bounds.ENV_CLEANUP_MARGIN,
        }
        return margin_map.get(self.category, 200)  # Default 200px

    def get_damage_margin(self):
        """
        Returns margin for hittable zone.
        Entity can take damage only when within this margin from screen edges.
        """
        margin_map = {
            EntityCategory.ENEMY: Bounds.ENEMY_DAMAGE_MARGIN,
            EntityCategory.ENVIRONMENT: Bounds.ENV_DAMAGE_MARGIN,
        }
        return margin_map.get(self.category, 0)  # Default: hittable immediately

    def is_offscreen(self):
        """
        Check if entity is far enough offscreen for cleanup.
        Tests all 4 edges using cleanup_margin.
        """
        m = self.get_cleanup_margin()
        return (self.rect.right < -m or
                self.rect.left > Display.WIDTH + m or
                self.rect.bottom < -m or
                self.rect.top > Display.HEIGHT + m)

    def is_hittable(self):
        """
        Check if entity is inside the damage zone (can receive collision damage).
        Used by collision manager before processing bullet hits.
        """
        m = self.get_damage_margin()
        return (self.rect.right > m and
                self.rect.left < Display.WIDTH - m and
                self.rect.bottom > m and
                self.rect.top < Display.HEIGHT - m)

    def has_tag(self, tag):
        """
        Check if entity has a specific tag or category.
        Allows checking both primary category and secondary tags.
        """
        return tag == self.category or tag in self.tags

    def __repr__(self) -> str:
        """Debug string representation of entity."""
        return (
            f"<{type(self).__name__} "
            f"pos=({self.pos.x:.1f}, {self.pos.y:.1f}) "
            f"tag={self.collision_tag} "
            f"category={getattr(self, 'category', '?')}>"
        )

    def setup_sprite(self, health, thresholds_dict, color_states, image_states=None, render_mode="shape"):
        """
        Initialize visual state system from config config.
        Auto-determines initial state from current health.

        Args:
            health: Current health value
            thresholds_dict: {"moderate": 2, "critical": 1}
            color_states: {"normal": (255,255,255), "damaged_moderate": ...}
            image_states: Optional {"normal": pygame.Surface, ...}
            render_mode: "shape" or "image"
        """
        # Get all state keys (ordered by threshold, highest first)
        sorted_states = sorted(
            thresholds_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Determine initial state from health
        state_key = None
        for name, threshold in sorted_states:
            if health <= threshold:
                state_key = f"damaged_{name}"
                break

        # Fallback to first color state if above all thresholds
        if state_key is None:
            state_key = next(iter(color_states.keys()))

        self._current_sprite = state_key
        self._sprite_config = {
            "thresholds": thresholds_dict,
            "colors": color_states,
            "images": image_states or {},
            "render_mode": render_mode
        }

    def get_current_color(self):
        """Get color for current visual state."""
        colors = self._sprite_config.get('colors', {})
        return colors.get(self._current_sprite, (255, 255, 255))

    def get_target_color(self, state_key):
        """Get color for target visual state."""
        colors = self._sprite_config.get('colors', {})
        return colors.get(state_key, (255, 255, 255))

    def get_current_image(self):
        """Get image for current visual state."""
        images = self._sprite_config.get('images', {})
        return images.get(self._current_sprite)

    def get_target_image(self, state_key):
        """Get image for target visual state."""
        images = self._sprite_config.get('images', {})
        return images.get(state_key)

    # ===========================================================
    # Rotation System
    # ===========================================================
    def update_rotation(self, velocity=None):
        """
        Rotate image to match velocity direction.
        Only rotates if velocity changed (optimization).

        Args:
            velocity: Optional velocity vector. If None, uses self.velocity.

        Usage:
            Subclasses should:
            1. Set self._rotation_enabled = True in __init__
            2. Call self.update_rotation() in update() or update_rotation(custom_vel)
        """
        if not self._rotation_enabled or self._base_image is None:
            return

        # Use provided velocity or fall back to self.velocity
        vel = velocity if velocity is not None else getattr(self, 'velocity', None)
        if vel is None or vel.length_squared() == 0:
            return

        # Calculate angle from velocity
        forward = pygame.Vector2(0, -1)  # Base sprite points up
        target_angle = forward.angle_to(vel)

        # Only rotate if angle changed (avoid unnecessary rotations)
        if abs(target_angle - self.rotation_angle) > 0.1:
            self.rotation_angle = target_angle
            self.image = pygame.transform.rotate(self._base_image, self.rotation_angle)
            # Update rect to match new rotated size
            old_center = self.rect.center
            self.rect = self.image.get_rect(center=old_center)
