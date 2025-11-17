"""
item_manager.py
---------------
Manages item spawning, loot tables, and drop chances.

Responsibilities
----------------
- Load item definitions from items.json
- Build weighted loot tables for random drops
- Listen for enemy death events and spawn items
- Handle item spawning via SpawnManager
"""

import random
from enum import Enum
import pygame
import os

from src.core.services.event_manager import EVENTS, EnemyDiedEvent
from src.core.services.config_manager import load_config
from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity


# ===========================================================
# Item Type Registry
# ===========================================================

class ItemType(Enum):
    """Enum for all available item types."""
    EXTRA_LIFE = "extra_life"
    SCORE_BONUS_MEDAL = "score_bonus_medal"
    HEALTH_PACK = "health_pack"
    QUICK_FIRE = "quick_fire"
    DUMMY = "dummy"


# ===========================================================
# Item Manager
# ===========================================================

class ItemManager:
    """Manages item definitions and spawning logic."""

    def __init__(self, spawn_manager, item_data_path: str):
        """
        Initialize item manager.

        Args:
            spawn_manager: Reference to SpawnManager for creating items
            item_data_path: Path to items.json configuration file
        """
        self.spawn_manager = spawn_manager
        self._item_definitions = {}
        self._loot_table_ids = []
        self._loot_table_weights = []

        # Load and build loot system
        self._load_item_definitions(item_data_path)
        self._build_loot_table()
        self._subscribe_to_events()

        DebugLogger.init("ItemManager initialized")

    # ===========================================================
    # Initialization
    # ===========================================================

    def _load_item_definitions(self, path: str) -> None:
        """Load item configurations from JSON file using ConfigManager."""
        self._item_definitions = load_config(path, default_dict={})

        if self._item_definitions:
            DebugLogger.init_sub(
                f"Loaded {len(self._item_definitions)} item definitions"
            )
        else:
            DebugLogger.warn(f"No items loaded from {path}")

    def _build_loot_table(self) -> None:
        """Build weighted loot table from item definitions."""
        for item_id, item_data in self._item_definitions.items():
            drop_weight = item_data.get("drop_weight", 0)

            if drop_weight > 0:
                # Convert string ID to enum
                try:
                    item_enum = ItemType(item_id)
                    self._loot_table_ids.append(item_enum)
                    self._loot_table_weights.append(drop_weight)
                except ValueError:
                    DebugLogger.warn(f"Unknown item type: {item_id}")

        DebugLogger.init_sub(
            f"Loot table built with {len(self._loot_table_ids)} items"
        )

    def _subscribe_to_events(self) -> None:
        """Subscribe to game events for item spawning."""
        EVENTS.subscribe(EnemyDiedEvent, self.on_enemy_died)

    # ===========================================================
    # Event Handlers
    # ===========================================================

    def on_enemy_died(self, event: EnemyDiedEvent) -> None:
        """Handle enemy death event - try to spawn item."""
        # For now, use hardcoded 15% drop chance
        self.try_spawn_random_item(
            position=event.position,
            drop_chance=0.35
        )

    # ===========================================================
    # Spawning Logic
    # ===========================================================

    def try_spawn_random_item(self, position: tuple, drop_chance: float) -> None:
        """Attempt to spawn a random item based on drop chance."""
        # Roll for drop
        if random.random() > drop_chance:
            return

        # Check if loot table has items
        if not self._loot_table_ids:
            DebugLogger.warn("No items in loot table")
            return

        # Select random item using weights
        selected_item = random.choices(
            self._loot_table_ids,
            weights=self._loot_table_weights,
            k=1
        )[0]

        # Spawn the item
        self.spawn_item(selected_item, position)

    def spawn_item(self, item_id: ItemType, position: tuple) -> None:
        """Spawn a specific item at given position."""
        # Get item definition
        item_data = self._item_definitions.get(item_id.value)
        if not item_data:
            DebugLogger.fail(f"Item definition not found: {item_id.value}")
            return

        # Load image if asset path exists
        image = None
        asset_path = item_data.get("asset_path")
        if asset_path:
            image = self._load_item_image(item_id.value, asset_path)

        # Spawn via SpawnManager
        x, y = position
        self.spawn_manager.spawn(
            "pickup",
            "default",
            x, y,
            item_data=item_data,
            image=image
        )

        DebugLogger.action(
            f"Spawned item '{item_id.value}' at ({x:.0f}, {y:.0f})",
            category="item"
        )

    def _load_item_image(self, item_id: str, asset_path: str) -> pygame.Surface:
        """Load and return item sprite image."""
        # Get size from item data
        item_data = self._item_definitions.get(item_id, {})
        size = item_data.get("size")

        # Calculate scale factor if size is specified
        scale = 1.0
        if size:
            temp_img = pygame.image.load(asset_path).convert_alpha() if os.path.exists(asset_path) else None
            if temp_img:
                scale = (size[0] / temp_img.get_width(), size[1] / temp_img.get_height())

        return BaseEntity.load_and_scale_image(asset_path, scale)
