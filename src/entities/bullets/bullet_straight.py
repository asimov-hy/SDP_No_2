"""
bullet_straight.py
------------------
Defines a simple straight-line bullet derived from BulletBase.

Responsibilities
----------------
- Move in a fixed linear path without rotation or targeting.
- Update and render through inherited BulletBase behavior.
- Provide an entry point for future visual or sound effects.
"""

from src.entities.bullets.bullet_base import BulletBase


class StraightBullet(BulletBase):
    """Basic straight-line bullet using default BulletBase movement."""

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt):
        """
        Update bullet movement and state each frame.

        Args:
            dt (float): Delta time (in seconds).
        """
        super().update(dt)
        # Future: Add trail effects or rotation if desired

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, surface):
        """
        Render the bullet using the base draw method.

        Args:
            surface (pygame.Surface): Surface to render on.
        """
        super().draw(surface)
        # Future: Add glow or directional effects here
