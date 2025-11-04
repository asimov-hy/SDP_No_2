"""
bullet_straight.py
------------------
Defines a simple straight-line bullets derived from BulletBase.

Responsibilities
----------------
- Move in a fixed linear path without rotation or targeting.
- Serve as the default projectile for player or enemy entities.
"""

from src.entities.bullets.bullet_base import BulletBase


class StraightBullet(BulletBase):
    """Basic straight-line bullets using default BulletBase movement."""
    pass
