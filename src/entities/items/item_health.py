"""
item_health.py
--------------
Example health pickup item.
"""

from .base_item import BaseItem
from src.entities.entity_state import EntityCategory

class ItemHealth(BaseItem):
    """Small health restore item."""

    __registry_category__ = EntityCategory.PICKUP
    __registry_name__ = "health"

    def __init__(self, x, y, draw_manager=None):
        """
        Initialize health pickup.

        Args:
            x (float): Spawn X position.
            y (float): Spawn Y position.
            draw_manager: Draw manager reference for shape optimization.
        """
        # Shape config: green circle
        shape_data = {
            "type": "circle",
            "color": (0, 255, 100),
            "size": (24, 24),
            "kwargs": {}
        }

        super().__init__(
            x, y,
            shape_data=shape_data,
            draw_manager=draw_manager,
            speed=60
        )

        self.heal_amount = 1

    def on_pickup(self, player):
        """Restore health to player."""
        print(f"Picked up item - Health +{self.heal_amount}")

        # Example health restoration (requires player health system)
        # if hasattr(player, 'health') and hasattr(player, 'max_health'):
        #     player.health = min(player.health + self.heal_amount, player.max_health)

    def reset(self, x, y, heal_amount=None, **kwargs):
        """
        Reset health item for pooling.

        Args:
            x: New X position
            y: New Y position
            heal_amount: Optional new heal amount
            **kwargs: Passed to BaseItem.reset()
        """
        # Reset base item
        super().reset(x, y, **kwargs)

        # Update heal amount if provided
        if heal_amount is not None:
            self.heal_amount = heal_amount