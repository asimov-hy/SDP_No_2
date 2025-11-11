"""
item.py
-------
Defines the pure data representation of an in-game item.
This class is intentionally decoupled from Pygame for portability and testability.
"""
import itertools

class Item:
    """
    A pure data container for an item's properties and state.
    It does not handle rendering or direct Pygame interactions.
    """
    # A counter to ensure each item instance has a unique ID, useful for tracking.
    _instance_counter = itertools.count()

    def __init__(self, item_id: str, position: tuple[int, int], item_data: dict):
        """
        Initializes a new item instance.

        Args:
            item_id (str): The unique identifier for the type of item (e.g., "health_potion").
            position (tuple[int, int]): The (x, y) coordinate of the item in the game world.
            item_data (dict): A dictionary containing the item's properties, loaded from JSON.
        """
        # Unique ID for this specific instance in the game world
        self.instance_id = next(self._instance_counter)

        # ID for the item's type/definition
        self.item_id = item_id
        
        # Core properties from data
        self.name = item_data.get("name", "Unknown Item")
        self.asset_path = item_data.get("asset_path")
        
        # Properties for collection-based effects and conditions
        self.conditions = item_data.get("conditions", [])
        self.effects = item_data.get("effects", [])

        # State
        self.position = position

    def update(self):
        """
        Updates the item's internal logic.
        This could include movement, timers, or other state changes.
        Current a placeholder, as ItemManager handles most logic.
        """
        pass

    def __repr__(self):
        return f"<Item(id={self.item_id}, instance_id={self.instance_id}, pos={self.position})>"
