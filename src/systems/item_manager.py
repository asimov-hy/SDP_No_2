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
from src.data.item_types import ItemType # Import ItemType

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
        self.dropped_items: list[Item] = []
        self._item_definitions = self._load_item_definitions(item_data_path)
        self._validate_item_types() # Call validation after loading definitions

    def _load_item_definitions(self, path: str) -> dict:
        """
        Loads item blueprints from a JSON file.

        Args:
            path (str): The path to the JSON file containing item definitions.

        Returns:
            dict: A dictionary of item definitions, keyed by item_id.
        """
        try:
            with open(path, 'r', encoding='utf-8') as f:
                definitions = json.load(f)
                if not definitions:
                    DebugLogger.warn(f"Item data file at '{path}' is empty.")
                else:
                    DebugLogger.system(f"Loaded {len(definitions)} item definitions from '{path}'.")
                return definitions
        except FileNotFoundError:
            DebugLogger.error(f"Item data file not found at '{path}'.")
            return {}
        except json.JSONDecodeError:
            DebugLogger.error(f"Could not decode JSON from '{path}'. Check file format.")
            return {}

    def _validate_item_types(self):
        """
        Validates that item IDs in ItemType are synchronized with items.json.
        Logs warnings for any discrepancies.
        """
        defined_in_code = set(ItemType.get_all())
        defined_in_json = set(self._item_definitions.keys())

        # Check for items defined in code but not in JSON
        missing_in_json = defined_in_code - defined_in_json
        for item_id in missing_in_json:
            DebugLogger.warn(f"ItemType '{item_id}' is defined in code but missing from items.json.")

        # Check for items defined in JSON but not in code
        missing_in_code = defined_in_json - defined_in_code
        for item_id in missing_in_code:
            DebugLogger.warn(f"Item '{item_id}' is defined in items.json but missing from ItemType.")

        if not missing_in_json and not missing_in_code:
            DebugLogger.system("ItemType and items.json are synchronized.")

    # ===========================================================
    # Public Methods for Item Lifecycle
    # ===========================================================
    def spawn_item(self, item_id: ItemType, position: tuple[int, int]):
        """
        Creates a new item instance and adds it to the active list.

        Args:
            item_id (str): The unique identifier for the type of item (e.g., "health_potion").
            position (tuple[int, int]): The (x, y) coordinate where the item should spawn.
        """
        item_data = self._item_definitions.get(item_id)
        if item_data:
            new_item = Item(item_id, position, item_data)
            self.dropped_items.append(new_item)
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
        for item in reversed(self.dropped_items):
            item.update()


