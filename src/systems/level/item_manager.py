"""
item_manager.py
----------------
Handles the data-driven aspects of in-game items, including loading
definitions, managing random drops, and applying collected item effects.

Responsibilities
----------------
- Load item definitions from an external data file (JSON).
- Act as a factory for creating new item instances via the SpawnManager.
- Manage a weighted loot table for random item drops.
- Process the global item effect queue and apply effects to the game state.
- Track all active item instances spawned by this manager.
"""
import json
import random
from datetime import datetime

import pygame
from src.entities.entity_registry import EntityRegistry
from src.entities.items.item import Item
EntityRegistry.register("pickup", "default", Item)
from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_state import STATE
from src.entities.items.item_definitions import ItemType, validate_item_data
from src.core.services.event_manager import EVENTS, EnemyDiedEvent, ItemCollectedEvent
from src.entities.enemies.base_enemy import BaseEnemy


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
        
        # Validate all item data at startup
        if validate_item_data(self._item_definitions):
            DebugLogger.system("Item data system successful.", category="system")
        else:
            DebugLogger.fail("Item data system failed with one or more warnings.", category="system")

        # Loot table for weighted random drops
        random.seed(int(datetime.now().timestamp()))
        self._loot_table_ids: list[ItemType] = []
        self._loot_table_weights: list[int] = []
        self._build_loot_table()

        self._subscribe_to_events() # Call subscription method

    def _subscribe_to_events(self):
        """Subscribes to relevant events from the event manager."""
        EVENTS.subscribe(EnemyDiedEvent, self.on_enemy_destroyed)
        EVENTS.subscribe(ItemCollectedEvent, self.on_item_collected)

    def on_item_collected(self, event: ItemCollectedEvent):
        """
        Handles the ItemCollectedEvent to apply item effects.
        
        Args:
            event (ItemCollectedEvent): The event containing the effects to apply.
        """
        for effect in event.effects:
            self.apply_effect(effect)

    def on_enemy_destroyed(self, event: EnemyDiedEvent):
        """
        Handles the OnEnemyDestroyed event to attempt spawning a random item.
        
        Args:
            event (EnemyDiedEvent): The event
        """
        if event:
            drop_chance = STATE.current_drop_chance
            self.try_spawn_random_item(
                position=event.position,
                drop_chance=drop_chance
            )

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
            asset_path = item_data.get("asset_path")
            loaded_image = self._load_item_image(item_id.value, asset_path)

            new_item = self.spawn_manager.spawn(
                category="pickup",
                type_name="default",
                x=position[0],
                y=position[1],
                item_data=item_data,
                image=loaded_image # Pass the loaded image
            )
            if new_item is None:
                return
            self.dropped_items.append(new_item)
            DebugLogger.trace(f"Spawned item '{item_id.value}' at {position}.", category="system")
        else:
            DebugLogger.warn(f"Attempted to spawn an unknown item_id: '{item_id.value}'")

    def _load_item_image(self, item_id: str, asset_path: str) -> pygame.Surface:
        """
        Loads and scales an item image from the given asset path.
        Provides a dummy image fallback if loading fails.

        Args:
            item_id (str): The ID of the item (for logging purposes).
            asset_path (str): The file path to the item's image asset.

        Returns:
            pygame.Surface: The loaded and scaled image, or a dummy surface on failure.
        """
        loaded_image = None
        if asset_path:
            try:
                loaded_image = pygame.image.load(asset_path).convert_alpha()
                loaded_image = pygame.transform.scale(loaded_image, (30, 30))
            except pygame.error as e:
                DebugLogger.warn(f"Failed to load item image '{asset_path}' for item '{item_id}': {e}", category="system")
        
        if loaded_image is None:
            DebugLogger.warn(f"Using dummy image for item '{item_id}'. Check asset_path: '{asset_path}'", category="system")
            loaded_image = pygame.Surface((30, 30)) # Fallback to dummy
        
        return loaded_image


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
        # Update existing items
        for item in reversed(self.dropped_items):
            item.update(dt)

    def apply_effect(self, effect: dict):
        """
        Applies a single item effect to the global game state.

        This method only handles effects that can be resolved by modifying
        the `GameState` directly (e.g., score, lives).

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
