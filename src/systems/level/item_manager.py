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

import pygame
from src.entities.entity_registry import EntityRegistry
from src.entities.items.item import Item
EntityRegistry.register("pickup", "default", Item)
from src.core.debug.debug_logger import DebugLogger
from src.entities.items.item_types import ItemType
from src.core.runtime.game_state import STATE

class ItemManager:
    """
    Handles the data-oriented aspects of items, acting as a database and factory.
    This manager is decoupled from rendering and direct entity dependencies.
    """
    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, spawn_manager=None, item_data_path: str = 'src/data/configs/items.json'):
        """
        Initializes the ItemManager.

        Args:
            spawn_manager: A reference to the spawn manager object.
            item_data_path (str): The path to the JSON file containing item definitions.
        """
        self.spawn_manager = spawn_manager
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
            DebugLogger.fail(f"Item data file not found at '{path}'.")
            return {}
        except json.JSONDecodeError:
            DebugLogger.fail(f"Could not decode JSON from '{path}'. Check file format.")
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
            new_item = self.spawn_manager.spawn(
                category="pickup",
                type_name="default",
                x=position[0],
                y=position[1],
                item_data=item_data,
                image=pygame.Surface((30, 30))
            )
            if new_item is None:
                return
            self.dropped_items.append(new_item)
            DebugLogger.trace(f"Spawned item '{item_id.value}' at {position}.", category="system")
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
            DebugLogger.trace(f"Randomly spawned '{selected_item_id.value}' at {position} from loot table.", category="system")
        except IndexError:
            DebugLogger.warn("Could not select an item from the loot table (it might be empty).")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Updates the logic for all dropped items and processes spawn/effect queues.
        """
        # Process spawn requests from the queue
        if STATE.item_spawn_requests:
            for request in STATE.item_spawn_requests:
                self.try_spawn_random_item(
                    position=request["position"],
                    drop_chance=request["drop_chance"]
                )
            STATE.item_spawn_requests.clear()

        # Update existing items
        for item in reversed(self.dropped_items):
            item.update(dt)

        # Process item effects from the queue
        if STATE.item_effect_queue:
            # Player reference is no longer passed to apply_effect
            for effects_list in STATE.item_effect_queue:
                for effect in effects_list:
                    self.apply_effect(effect) # No player argument here

            STATE.item_effect_queue.clear()

    def apply_effect(self, effect: dict):
        """
        Applies a single item effect to the game state.
        Effects that require direct player manipulation are passed for now.

        Args:
            effect (dict): The effect dictionary from items.json.
        """
        effect_type = effect.get("type")
        match effect_type:
            case "ADD_SCORE":
                amount = effect.get("amount", 0)
                STATE.score += amount
                DebugLogger.system(f"Score increased by {amount}. Total score: {STATE.score}", category="system")

            case "ADD_LIVES":
                amount = effect.get("amount", 0)
                STATE.lives += amount
                DebugLogger.system(f"Lives increased by {amount}. Total lives: {STATE.lives}", category="system")

            case _:
                DebugLogger.warn(f"Unknown item effect type: '{effect_type}'", category="system")
