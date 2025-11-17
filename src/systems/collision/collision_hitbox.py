"""
collision_hitbox.py
-------------------
Defines the Hitbox class used by all active entities_animation to provide
modular and scalable collision detection bounds.

Responsibilities
----------------
- Maintain a scaled collision rectangle separate from the visual sprite.
- Follow the parent entity's position and size automatically.
- Support optional debug visualization for development.
- Support dynamic hitbox modifications for animations and abilities.

Sizing Modes
------------
Automatic Mode (Default):
    Hitbox size is calculated from owner.rect * scale.
    Size updates automatically when owner.rect changes.

Manual Mode:
    Hitbox size is set explicitly and doesn't change.
    Owner.rect changes are ignored until set_scale() is called.

Common Patterns
---------------
Static hitbox: CollisionHitbox(entity, scale=1.0)
Animation-driven: CollisionHitbox(entity, scale=0.9)
Ability animation_effects: hitbox.set_size(4, 4) then hitbox.reset()
Directional attacks: hitbox.set_offset(8, 0) for forward extension
"""

import pygame
from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Debug


class CollisionHitbox:
    """Represents a rectangular collision boundary tied to an entity."""

    __slots__ = (
        "owner", "scale", "offset", "rect",
        "_size_cache", "_color_cache", "active",
        "_manual_size",
        "shape", "shape_params",
        "_shape_width", "_shape_height", "_shape_radius",
        "_rotation",  # Cached entity rotation
        "use_obb", "_obb_corners"  # OBB support
    )

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, owner, scale: float = 1.0, offset=(0, 0), shape='rect', shape_params=None):
        """
        Initialize a hitbox for the given entity.

        Args:
            owner: The parent entity this hitbox belongs to.
            scale: Proportional size relative to owner sprite (0.0-1.0+).
            offset: (x, y) offset from owner center in pixels.
            shape: Hitbox shape type ('rect', 'circle', 'polygon').
            shape_params: Dict with shape-specific overrides (width, height, radius, points).
        """
        # Basic setup
        self.owner = owner
        self.scale = scale
        self.offset = pygame.Vector2(offset)

        # Shape configuration
        self.shape = shape
        self.shape_params = shape_params or {}

        # Shape-specific overrides
        self._shape_width = None
        self._shape_height = None
        self._shape_radius = None

        # Rotation tracking
        self._rotation = 0.0  # Cached rotation in degrees
        self.use_obb = False  # Enable OBB for non-axis-aligned rotation
        self._obb_corners = None  # Cached OBB corner points

        # Core attributes
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.active = True
        self._manual_size = False

        # Cached config
        self._size_cache = None
        self._color_cache = self._cache_color()

        if hasattr(owner, "rect"):
            self._initialize_from_owner()
        else:
            DebugLogger.warn(f"{type(owner).__name__} missing 'rect' attribute!")

        # DebugLogger.init_entry(f"{self.owner} CollisionHitbox Initialized")

    # ===========================================================
    # Internal Setup
    # ===========================================================
    def _initialize_from_owner(self):
        """Initialize hitbox dimensions based on shape type."""
        rect = self.owner.rect

        if self.shape == 'rect':
            self._init_rect_hitbox(rect)
        elif self.shape == 'circle':
            self._init_circle_hitbox(rect)
        elif self.shape == 'polygon':
            self._init_polygon_hitbox(rect)
        else:
            DebugLogger.warn(f"Unknown hitbox shape '{self.shape}', defaulting to rect")
            self._init_rect_hitbox(rect)

    def _init_rect_hitbox(self, rect):
        """Initialize rectangular hitbox with manual width/height override support."""
        # Manual overrides take priority over scale
        w = self.shape_params.get('width')
        h = self.shape_params.get('height')

        if w is not None and h is not None:
            # Both manual dimensions provided
            self._shape_width = w
            self._shape_height = h
            self._manual_size = True
        elif w is not None:
            # Only width manual, scale height
            self._shape_width = w
            self._shape_height = int(rect.height * self.scale)
            self._manual_size = True
        elif h is not None:
            # Only height manual, scale width
            self._shape_width = int(rect.width * self.scale)
            self._shape_height = h
            self._manual_size = True
        else:
            # No manual overrides, use scale
            self._shape_width = int(rect.width * self.scale)
            self._shape_height = int(rect.height * self.scale)

        self.rect.size = (self._shape_width, self._shape_height)
        self.rect.center = (rect.centerx + self.offset.x, rect.centery + self.offset.y)
        self._size_cache = (self._shape_width, self._shape_height)

    def _init_circle_hitbox(self, rect):
        """Initialize circular hitbox (stored as bounding rect)."""
        # Manual radius or auto-calculate from smallest dimension
        radius = self.shape_params.get('radius')

        if radius is not None:
            self._shape_radius = radius
            self._manual_size = True
        else:
            # Auto-scale from smallest entity dimension
            self._shape_radius = int(min(rect.width, rect.height) * self.scale / 2)

        diameter = self._shape_radius * 2
        self.rect.size = (diameter, diameter)
        self.rect.center = (rect.centerx + self.offset.x, rect.centery + self.offset.y)
        self._size_cache = (diameter, diameter)

    def _init_polygon_hitbox(self, rect):
        """Initialize polygon hitbox (bounding box for now)."""
        points = self.shape_params.get('points', [])

        if not points:
            DebugLogger.warn("Polygon hitbox missing 'points', falling back to rect")
            self._init_rect_hitbox(rect)
            return

        # Calculate bounding box from points
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        bbox_w = max(xs) - min(xs)
        bbox_h = max(ys) - min(ys)

        # Apply scale to bounding box
        self._shape_width = int(bbox_w * self.scale)
        self._shape_height = int(bbox_h * self.scale)
        self._manual_size = True

        self.rect.size = (self._shape_width, self._shape_height)
        self.rect.center = (rect.centerx + self.offset.x, rect.centery + self.offset.y)
        self._size_cache = (self._shape_width, self._shape_height)

    def _cache_color(self):
        """Cache debug color based on entity tag for faster draw calls."""
        tag = getattr(self.owner, "collision_tag", "neutral")
        if "enemy" in tag:
            return 255, 60, 60
        if "player" in tag:
            return 60, 160, 255
        return 80, 255, 80

    def _rotate_offset(self, x, y, angle_degrees):
        """
        Rotate offset vector by entity rotation.

        Args:
            x: X component of offset
            y: Y component of offset
            angle_degrees: Rotation angle in degrees

        Returns:
            tuple: (rotated_x, rotated_y)
        """
        # Early exit for no rotation
        if angle_degrees == 0:
            return (x, y)

        import math
        radians = math.radians(angle_degrees)
        cos_a = math.cos(radians)
        sin_a = math.sin(radians)

        # Rotation matrix application
        rotated_x = x * cos_a - y * sin_a
        rotated_y = x * sin_a + y * cos_a

        return (rotated_x, rotated_y)

    # ===========================================================
    # Update Cycle
    # ===========================================================
    def update(self):
        """
        Synchronize the hitbox position and size with the owner entity.
        Called once per frame before collision checks.
        """
        rect = getattr(self.owner, "rect", None)

        if not rect:
            DebugLogger.warn(f"[Hitbox] {type(self.owner).__name__} lost rect reference")
            return

        # Update rotation from entity and check if OBB needed
        old_rotation = self._rotation
        self._rotation = getattr(self.owner, 'rotation_angle', 0.0)

        # Detect rotation change and update OBB state
        if abs(self._rotation - old_rotation) > 0.1:
            self.use_obb = (self._rotation % 90 != 0)
            self._obb_corners = None  # Invalidate cache

        # Only recalculate size if in automatic mode
        if not self._manual_size:
            if self.shape == 'rect':
                self._update_rect_size(rect)
            elif self.shape == 'circle':
                self._update_circle_size(rect)
            # Polygon doesn't auto-resize

        # Apply rotated offset to position
        rotated_offset = self._rotate_offset(self.offset.x, self.offset.y, self._rotation)
        self.rect.centerx = rect.centerx + rotated_offset[0]
        self.rect.centery = rect.centery + rotated_offset[1]

    def _update_rect_size(self, rect):
        """Recalculate rect hitbox size if entity rect changed."""
        # Only recalculate if no manual overrides
        if self._shape_width is None:
            w = int(rect.width * self.scale)
        else:
            w = self._shape_width

        if self._shape_height is None:
            h = int(rect.height * self.scale)
        else:
            h = self._shape_height

        if (w, h) != self._size_cache:
            self.rect.size = (w, h)
            self._size_cache = (w, h)

    def _update_circle_size(self, rect):
        """Recalculate circle hitbox size if entity rect changed."""
        if self._shape_radius is None:
            # Auto-recalculate from entity size
            radius = int(min(rect.width, rect.height) * self.scale / 2)
        else:
            # Use manual radius
            radius = self._shape_radius

        diameter = radius * 2
        if (diameter, diameter) != self._size_cache:
            self.rect.size = (diameter, diameter)
            self._size_cache = (diameter, diameter)

    def get_center(self):
        """
        Get the center point of the hitbox.

        Returns:
            tuple: (center_x, center_y)
        """
        return (self.rect.centerx, self.rect.centery)

    def get_obb_corners(self):
        """
        Calculate and return the 4 corner points of the oriented bounding box.
        Uses cached corners if rotation hasn't changed.

        Returns:
            list: [(x1, y1), (x2, y2), (x3, y3), (x4, y4)] - four corner points
        """
        # Return cached corners if valid
        if self._obb_corners is not None:
            return self._obb_corners

        # Get center and half-dimensions
        cx, cy = self.get_center()
        half_w = self.rect.width / 2
        half_h = self.rect.height / 2

        # If no rotation or axis-aligned, return AABB corners
        if self._rotation % 90 == 0:
            self._obb_corners = [
                (cx - half_w, cy - half_h),  # Top-left
                (cx + half_w, cy - half_h),  # Top-right
                (cx + half_w, cy + half_h),  # Bottom-right
                (cx - half_w, cy + half_h)  # Bottom-left
            ]
            return self._obb_corners

        # Calculate rotated corners
        import math
        radians = math.radians(self._rotation)
        cos_a = math.cos(radians)
        sin_a = math.sin(radians)

        # Local corner offsets (unrotated)
        local_corners = [
            (-half_w, -half_h),  # Top-left
            (half_w, -half_h),  # Top-right
            (half_w, half_h),  # Bottom-right
            (-half_w, half_h)  # Bottom-left
        ]

        # Rotate each corner and translate to world space
        self._obb_corners = []
        for lx, ly in local_corners:
            # Apply rotation matrix
            rx = lx * cos_a - ly * sin_a
            ry = lx * sin_a + ly * cos_a
            # Translate to world position
            self._obb_corners.append((cx + rx, cy + ry))

        return self._obb_corners

    # ===========================================================
    # Dynamic Hitbox Control
    # ===========================================================
    def set_size(self, width: int, height: int):
        """
        Manually set hitbox dimensions (ignores owner rect and scale).
        Switches to manual mode until set_scale() is called.

        Args:
            width: New hitbox width in pixels (must be > 0).
            height: New hitbox height in pixels (must be > 0).
        """
        if width <= 0 or height <= 0:
            DebugLogger.warn(f"Invalid size ({width}, {height}) - must be positive")
            return

        self._manual_size = True  # Enable manual mode
        self.rect.size = (width, height)
        self._size_cache = (width, height)
        # Preserve center position
        self.rect.center = (
            self.owner.rect.centerx + self.offset.x,
            self.owner.rect.centery + self.offset.y
        )

    def set_offset(self, x: float, y: float):
        """
        Change hitbox offset from owner's center.

        Args:
            x: X offset from owner center in pixels.
            y: Y offset from owner center in pixels.
        """
        self.offset.x = x
        self.offset.y = y

        # Apply rotation to new offset
        rotated_offset = self._rotate_offset(self.offset.x, self.offset.y, self._rotation)
        self.rect.center = (
            self.owner.rect.centerx + rotated_offset[0],
            self.owner.rect.centery + rotated_offset[1]
        )

    def set_scale(self, scale: float):
        """
        Change hitbox scale relative to owner's rect.
        Returns to automatic sizing mode.

        Args:
            scale: New scale multiplier (must be > 0).
        """
        if scale <= 0:
            DebugLogger.warn(f"Invalid scale {scale} - must be positive")
            return

        self._manual_size = False  # Return to automatic mode
        self.scale = scale

        # Force immediate recalculation
        if hasattr(self.owner, "rect"):
            rect = self.owner.rect
            scaled_w, scaled_h = int(rect.width * scale), int(rect.height * scale)
            self.rect.size = (scaled_w, scaled_h)
            self._size_cache = (scaled_w, scaled_h)
            self.rect.center = (
                rect.centerx + self.offset.x,
                rect.centery + self.offset.y
            )

    def reset(self):
        """
        Reset hitbox to original owner rect size and scale.

        Useful for:
            - Ending temporary ability animation_effects
            - Reverting after animation sequences
            - Debug/testing
        """
        self._manual_size = False
        self._size_cache = None
        self._initialize_from_owner()
        DebugLogger.trace(f"[Hitbox] Reset for {type(self.owner).__name__}")

    # ===========================================================
    # State Inspection
    # ===========================================================
    @property
    def is_manual_mode(self) -> bool:
        """Check if hitbox is in manual sizing mode."""
        return self._manual_size

    def get_size(self) -> tuple[int, int]:
        """Get current hitbox dimensions as (width, height)."""
        return self.rect.width, self.rect.height

    def get_offset(self) -> tuple[float, float]:
        """Get current hitbox offset as (x, y)."""
        return self.offset.x, self.offset.y

    # ===========================================================
    # Activation Control
    # ===========================================================
    def set_active(self, active: bool):
        """
        Enable or disable collision participation for this hitbox.

        Args:
            active (bool): True to activate collision, False to disable.
        """
        self.active = active
        state = "enabled" if active else "disabled"
        DebugLogger.state(f"Hitbox {state} for {type(self.owner).__name__}", category="animation_effects")

    # ===========================================================
    # Debug Visualization
    # ===========================================================
    def draw_debug(self, surface):
        """
        Render a visible outline of the hitbox for debugging.
        Shows AABB (green/colored) and OBB (red) when rotation is active.

        Args:
            surface (pygame.Surface or DrawManager): The rendering surface to draw onto.
        """
        if not Debug.HITBOX_VISIBLE:
            return

        # Draw AABB - use DrawManager queue if available
        if hasattr(surface, "queue_hitbox"):
            surface.queue_hitbox(self.rect, color=self._color_cache, width=Debug.HITBOX_LINE_WIDTH)
            # Draw OBB directly to DrawManager's surface if available
            if self.use_obb and hasattr(surface, 'surface') and surface.surface:
                corners = self.get_obb_corners()
                pygame.draw.lines(surface.surface, (255, 0, 0), True, corners, 2)
        # Fallback — direct draw to pygame.Surface
        elif isinstance(surface, pygame.Surface):
            pygame.draw.rect(surface, self._color_cache, self.rect, Debug.HITBOX_LINE_WIDTH)
            # Draw OBB
            if self.use_obb:
                corners = self.get_obb_corners()
                pygame.draw.lines(surface, (255, 0, 0), True, corners, 2)
        else:
            DebugLogger.warn(f"Invalid debug hitbox draw: {type(surface).__name__}")
