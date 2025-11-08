"""
collision_hitbox.py
---------
Defines the Hitbox class used by all active entities to provide
modular and scalable collision detection bounds.

Responsibilities
----------------
- Maintain a scaled collision rectangle separate from the visual sprite.
- Follow the parent entity's position and size automatically.
- Support optional debug visualization for development.
"""

import pygame
from src.core.utils.debug_logger import DebugLogger
from src.core.game_settings import Debug


class CollisionHitbox:
    """Represents a rectangular collision boundary tied to an entity."""

    __slots__ = ("owner", "scale", "offset", "rect", "_size_cache", "_color_cache")

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, owner, scale: float = 1.0, offset=(0, 0)):
        """
        Initialize a hitbox for the given entity.

        Args:
            owner: The parent entity this hitbox belongs to.
            scale (float): Proportional size of the hitbox relative to the sprite (e.g., 0.85).
            offset (tuple[float, float]): Additional offset applied to the hitbox center.
        """
        self.owner = owner
        self.scale = scale
        self.offset = pygame.Vector2(offset)
        self.rect = pygame.Rect(0, 0, 0, 0)
        self._size_cache = None
        self._color_cache = None

        if hasattr(owner, "rect"):
            self._initialize_from_owner()
            self._cache_color()
            # DebugLogger.init(f"[Hitbox] Created for {type(owner).__name__} | Scale={scale} | Offset={offset}")
        else:
            DebugLogger.warn(f"[Hitbox] {type(owner).__name__} missing 'rect' attribute!")

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
            self._color_cache = (255, 60, 60)
        elif "player" in tag:
            self._color_cache = (60, 160, 255)
        else:
            self._color_cache = (80, 255, 80)

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
            DebugLogger.warn_once(f"[Hitbox] {type(self.owner).__name__} lost rect reference")
            return

        # Recalculate only if size changed
        scaled_w, scaled_h = int(rect.width * self.scale), int(rect.height * self.scale)
        if (scaled_w, scaled_h) != self._size_cache:
            self.rect.size = (scaled_w, scaled_h)
            self._size_cache = (scaled_w, scaled_h)

        self.rect.centerx = rect.centerx + self.offset.x
        self.rect.centery = rect.centery + self.offset.y

        if Debug.VERBOSE_HITBOX_UPDATE:
            DebugLogger.trace(f"[Hitbox] Updated {type(self.owner).__name__} → {self.rect.center}")

    # ===========================================================
    # Debug Visualization
    # ===========================================================
    def draw_debug(self, surface):
        """
        Render a visible outline of the hitbox for debugging.

        Args:
            surface (pygame.Surface): The rendering surface to draw onto.
        """
        if not Debug.ENABLE_HITBOX:
            return

        pygame.draw.rect(surface, self._color_cache, self.rect, 1)

        if Debug.VERBOSE_HITBOX_DRAW:
            DebugLogger.trace(
                f"[Hitbox] Drawn {type(self.owner).__name__} at {self.rect.center}"
            )