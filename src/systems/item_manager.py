"""
item_manager.py
----------------
Manages the lifecycle of all item data objects in the game.

Responsibilities
----------------
- Loading item definitions from an external data file (JSON).
- Creating new item instances in the game world (Factory role).
- Tracking all active item instances.
- Removing items that have been collected or expired.
"""
import json
from src.entities.items.item import Item
from src.core.utils.debug_logger import DebugLogger

class ItemManager:
    """
    Handles the data-oriented aspects of items, acting as a database and factory.
    This manager is decoupled from rendering and direct entity dependencies.
    """
    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, game_state=None, item_data_path: str = 'src/data/items.json'):
        """
        Initializes the ItemManager.

        Args:
            game_state: A reference to the global game state object.
            item_data_path (str): The path to the JSON file containing item definitions.
        """
        self.game_state = game_state
        self.active_items: list[Item] = []
        self._item_definitions = self._load_item_definitions(item_data_path)

    def _load_item_definitions(self, path: str) -> dict:
        """
        Loads item blueprints from a JSON file.

        Args:
            path (str): The path to the JSON file containing item definitions.

        Returns:
            dict: A dictionary of item definitions, keyed by item_id.
        """

    # ===========================================================
    # Public Methods for Item Lifecycle
    # ===========================================================
    def spawn_item(self, item_id: str, position: tuple[int, int]):
        """
        Creates a new item instance and adds it to the active list.

        Args:
            item_id (str): The unique identifier for the type of item (e.g., "health_potion").
            position (tuple[int, int]): The (x, y) coordinate where the item should spawn.
        """
        item_data = self._item_definitions.get(item_id)
        if item_data:
            new_item = Item(item_id, position, item_data)
            self.active_items.append(new_item)
            DebugLogger.info(f"Spawned item '{item_id}' at {position}.")
        else:
            DebugLogger.warn(f"Attempted to spawn an unknown item_id: '{item_id}'")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self):
        """
        Updates the logic for all active items.

        Args:
            ...
        """
        for item in reversed(self.active_items):
            item.update()


