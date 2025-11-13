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
        "_manual_size"
    )

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, owner, scale: float = 1.0, offset=(0, 0)):
        """
        Initialize a hitbox for the given entity.

        Args:
            owner: The parent entity this hitbox belongs to.
            scale: Proportional size relative to owner sprite (0.0-1.0+).
            offset: (x, y) offset from owner center in pixels.
        """
        # Basic setup
        self.owner = owner
        self.scale = scale
        self.offset = pygame.Vector2(offset)

        # Core attributes
        self.rect = pygame.Rect(0, 0, 0, 0)
        self.active = True
        self._manual_size = False

        # Cached data
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
        """Initialize hitbox dimensions based on the owner's sprite rect."""
        rect = self.owner.rect
        scaled_size = (int(rect.width * self.scale), int(rect.height * self.scale))
        self.rect.size = scaled_size
        self.rect.center = (rect.centerx + self.offset.x, rect.centery + self.offset.y)
        self._size_cache = scaled_size

    def _cache_color(self):
        """Cache debug color based on entity tag for faster draw calls."""
        tag = getattr(self.owner, "collision_tag", "neutral")
        if "enemy" in tag:
            return 255, 60, 60
        if "player" in tag:
            return 60, 160, 255
        return 80, 255, 80

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

        # Only recalculate size if in automatic mode
        if not self._manual_size:
            scaled_w, scaled_h = int(rect.width * self.scale), int(rect.height * self.scale)
            if (scaled_w, scaled_h) != self._size_cache:
                self.rect.size = (scaled_w, scaled_h)
                self._size_cache = (scaled_w, scaled_h)

        # Always update position
        self.rect.centerx = rect.centerx + self.offset.x
        self.rect.centery = rect.centery + self.offset.y

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

        self.rect.center = (
            self.owner.rect.centerx + self.offset.x,
            self.owner.rect.centery + self.offset.y
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

        Args:
            surface (pygame.Surface): The rendering surface to draw onto.
        """
        if not Debug.HITBOX_VISIBLE:
            return

        # DrawManager integration (preferred)
        if hasattr(surface, "queue_hitbox"):
            surface.queue_hitbox(self.rect, color=self._color_cache, width=Debug.HITBOX_LINE_WIDTH)
            return

        # Case 2: Fallback — direct draw to pygame.Surface
        if isinstance(surface, pygame.Surface):
            pygame.draw.rect(surface, self._color_cache, self.rect, Debug.HITBOX_LINE_WIDTH)
        else:
            DebugLogger.warn(f"Invalid debug hitbox draw: {type(surface).__name__}")

