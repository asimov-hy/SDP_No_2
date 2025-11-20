"""
base_obstacle.py
----------------
Base class for physical objects that can block/bounce projectiles and entities.
Examples: walls, asteroids, destructible barriers.
"""

from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory


class BaseObstacle(BaseEntity):
    """
    Base class for physical obstacles.

    Examples: walls, asteroids, barriers, pushable blocks.
    Can be static or moving, destructible or indestructible.
    """

    __slots__ = (
        'is_destructible', 'blocks_bullets', 'blocks_movement',
        'health', 'max_health'
    )

    def __init__(self, x, y, is_destructible=False, **kwargs):
        """
        Initialize obstacle.

        Args:
            x, y: Center position
            is_destructible: Whether obstacle can be destroyed by damage
            **kwargs: Passed to BaseEntity (image, shape_data, etc.)
        """
        super().__init__(x, y, **kwargs)
        self.category = EntityCategory.OBSTACLE
        self.collision_tag = "obstacle"

        # Physics properties
        self.is_destructible = is_destructible
        self.blocks_bullets = True
        self.blocks_movement = True

        # Health (if destructible)
        self.health = 0
        self.max_health = 0

        if is_destructible:
            # Subclasses should set appropriate health values
            self.health = 1
            self.max_health = 1

    def take_damage(self, amount):
        """
        Apply damage to obstacle (if destructible).

        Args:
            amount: Damage value

        Returns:
            bool: True if obstacle was destroyed
        """
        if not self.is_destructible:
            return False

        self.health -= amount

        if self.health <= 0:
            self.mark_dead()
            return True

        return False

    def update(self, dt):
        """
        Base update - obstacles are typically static.
        Override for moving obstacles.
        """
        pass