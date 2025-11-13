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
- Handling weighted random item drops.
"""
import json
import random
from src.entities.items.item import Item
from src.core.utils.debug_logger import DebugLogger
from src.data.item_types import ItemType

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
        self._validate_item_types()

        # Loot table for weighted random drops
        self._loot_table_ids: list[ItemType] = []
        self._loot_table_weights: list[int] = []
        self._build_loot_table()

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

        missing_in_json = defined_in_code - defined_in_json
        for item_id in missing_in_json:
            DebugLogger.warn(f"ItemType '{item_id}' is defined in code but missing from items.json.")

        missing_in_code = defined_in_json - defined_in_code
        for item_id in missing_in_code:
            DebugLogger.warn(f"Item '{item_id}' is defined in items.json but missing from ItemType.")

        if not missing_in_json and not missing_in_code:
            DebugLogger.system("ItemType and items.json are synchronized.")

    def _build_loot_table(self):
        """
        Parses item definitions to build a weighted loot table for random drops.
        """
        DebugLogger.system("Building item loot table...")
        for item_id, data in self._item_definitions.items():
            weight = data.get("drop_weight", 0)
            if weight > 0:
                try:
                    item_type = ItemType(item_id)
                    self._loot_table_ids.append(item_type)
                    self._loot_table_weights.append(weight)
                except ValueError:
                    DebugLogger.warn(f"Item '{item_id}' in items.json has a drop_weight but is not a valid ItemType.")
        
        if self._loot_table_ids:
            DebugLogger.system(f"Loot table built with {len(self._loot_table_ids)} item(s).")
        else:
            DebugLogger.warn("Loot table is empty. No items have 'drop_weight' > 0 in items.json.")

    # ===========================================================
    # Public Methods for Item Lifecycle
    # ===========================================================
    def spawn_item(self, item_id: ItemType, position: tuple[int, int]):
        """
        Creates a new item instance and adds it to the active list.

        Args:
            item_id (ItemType): The unique identifier for the type of item.
            position (tuple[int, int]): The (x, y) coordinate where the item should spawn.
        """
        item_data = self._item_definitions.get(item_id.value)
        if item_data:
            new_item = Item(item_id, position, item_data)
            self.dropped_items.append(new_item)
            DebugLogger.info(f"Spawned item '{item_id.value}' at {position}.")
        else:
            DebugLogger.warn(f"Attempted to spawn an unknown item_id: '{item_id.value}'")

    def try_spawn_random_item(self, position: tuple[int, int], drop_chance: float = 0.15):
        """
        Attempts to spawn a random item based on a weighted loot table.

        First, it checks against `drop_chance` to see if any item should drop at all.
        If successful, it selects an item from the loot table based on its weight.

        Args:
            position (tuple): The (x, y) coordinate where the item should spawn.
            drop_chance (float): The base probability (0.0 to 1.0) that an item will drop.
        """
        if not (random.random() < drop_chance):
            return

        if not self._loot_table_ids:
            return

        try:
            selected_item_id = random.choices(
                self._loot_table_ids,
                weights=self._loot_table_weights,
                k=1
            )[0]
            self.spawn_item(selected_item_id, position)
            DebugLogger.info(f"Randomly spawned '{selected_item_id.value}' at {position} from loot table.")
        except IndexError:
            DebugLogger.warn("Could not select an item from the loot table (it might be empty).")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self):
        """
        Updates the logic for all dropped items.
        """
        for item in reversed(self.dropped_items):
            item.update()
