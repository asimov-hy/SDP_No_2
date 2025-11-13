"""
item_health.py
--------------
Example health pickup item.
"""

from .base_item import BaseItem


class HealthPickup(BaseItem):
    """Small health restore item."""

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
            "size": (12, 12),
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