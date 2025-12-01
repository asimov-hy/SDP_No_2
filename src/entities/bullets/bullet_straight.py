"""
bullet_straight.py
------------------
Defines a basic straight-line bullet derived from BaseBullet.

Responsibilities
----------------
- Moves in a fixed linear path.
- Relies entirely on BaseBullet for motion, rendering, and collision.
- Provides a clean subclass entry point for visual or behavioral extensions.
"""

from src.entities.bullets.base_bullet import BaseBullet
from src.entities.entity_types import EntityCategory


class StraightBullet(BaseBullet):
    """Simple bullet that travels in a straight line."""

    __registry_category__ = EntityCategory.PROJECTILE
    __registry_name__ = "straight"

    __slots__ = ()

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, *args, **kwargs):
        """Initialize a straight-line bullet instance."""
        super().__init__(*args, **kwargs)

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Move linearly according to BaseBullet velocity.
        Override if extended behaviors (e.g., trails, acceleration) are added.
        """
        super().update(dt)

        # Future extensions:
        # - Add sprite rotation based on velocity vector.
        # - Add glow/trail or hit effects emitters.

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Queue this bullet for rendering via DrawManager.

        Uses BaseBullet's drawing behavior to ensure consistent layering.
        """
        super().draw(draw_manager)
        # Future: Add glow, flicker, or material animation_effects here.
