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
from src.core.settings import Debug


class CollisionHitbox:
    """Represents a rectangular collision boundary tied to an entity."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, owner, scale: float = 1.0, offset=(0, 0)):
        """
        Initialize a hitbox for the given entity.

        Args:
            owner: The parent entity this hitbox belongs to.
            scale (float): Proportional size of the hitbox relative to the entity sprite.
                           Example: 0.85 → 85% of the sprite’s width and height.
            offset (tuple[float, float]): Positional offset applied to the hitbox center.
        """
        self.owner = owner
        self.scale = scale
        self.offset = pygame.Vector2(offset)
        self.rect = self._compute_rect()

        DebugLogger.init(
            f"Created Hitbox for {type(owner).__name__} | Scale={scale} | Offset={offset}"
        )

    # ===========================================================
    # Internal Computation
    # ===========================================================
    def _compute_rect(self) -> pygame.Rect:
        """
        Compute a scaled rectangle based on the owner's current sprite rect.

        Returns:
            pygame.Rect: The calculated hitbox rectangle.
        """
        base_rect = getattr(self.owner, "rect", None)
        if base_rect is None:
            DebugLogger.warn(f"[Hitbox] {type(self.owner).__name__} missing rect attribute.")
            return pygame.Rect(0, 0, 0, 0)

        width = int(base_rect.width * self.scale)
        height = int(base_rect.height * self.scale)

        hitbox = pygame.Rect(0, 0, width, height)
        hitbox.center = base_rect.center + self.offset
        return hitbox

    # ===========================================================
    # Update Cycle
    # ===========================================================
    def update(self):
        """
        Synchronize the hitbox position and dimensions with the owner.
        Should be called once per frame, typically before collision checks.
        """
        if not hasattr(self.owner, "rect"):
            return

        self.rect = self._compute_rect()

        if Debug.VERBOSE_HITBOX_UPDATE:
            DebugLogger.trace(
                f"Hitbox updated ({type(self.owner).__name__}) → Center={self.rect.center}"
            )

    # ===========================================================
    # Rendering (Debug Only)
    # ===========================================================
    def draw_debug(self, surface):
        """
        Render a visual outline of the hitbox for debugging purposes.

        Args:
            surface (pygame.Surface): The rendering surface to draw onto.
        """
        if not getattr(Debug, "ENABLE_HITBOX", False):
            return

        if hasattr(self.owner, "owner") and getattr(self.owner, "owner") == "enemy":
            color = (255, 0, 0)  # Red for enemies
        elif hasattr(self.owner, "owner") and getattr(self.owner, "owner") == "player":
            color = (0, 128, 255)  # Blue for player bullets
        else:
            color = (0, 255, 0)  # Green default (player, enemies)

        pygame.draw.rect(surface, color, self.rect, 1)

        if Debug.VERBOSE_HITBOX_DRAW:
            DebugLogger.trace(
                f"Drew hitbox outline for {type(self.owner).__name__} at {self.rect.center}"
            )

