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

from src.core.services.event_manager import get_events, EnemyDiedEvent
from src.core.services.config_manager import load_config
from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.items.base_item import BaseItem


# ===========================================================
# Item Type Registry
# ===========================================================

class ItemType(Enum):
    """Enum for all available item types."""
    HEAL = "heal"
    QUICK_FIRE = "quick_fire"
    NUKE = "nuke"
    SPEED_BOOST = "speed_boost"


# ===========================================================
# Item Manager
# ===========================================================

class ItemManager:
    """Manages item definitions and spawning logic."""

    ASSET_BASE_PATH = "assets/images/sprites/items/"
    DEFAULT_ITEM_SIZE = (48, 48)

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
        self._fallback_image = None

        # Load and build loot system
        self._load_item_definitions(item_data_path)
        self._build_loot_table()
        self._subscribe_to_events()
        self._image_cache = {}
        self._load_fallback_image()

        DebugLogger.init("ItemManager initialized")

    # ===========================================================
    # Initialization
    # ===========================================================

    def _load_item_definitions(self, path: str) -> None:
        """Load item configurations from JSON file using ConfigManager."""
        self._item_definitions = load_config(path, default_dict={})

        if self._item_definitions:
            # Auto-inject default size if missing explicit size or scale
            for item_id, item_data in self._item_definitions.items():
                if "size" not in item_data and "scale" not in item_data:
                    item_data["size"] = self.DEFAULT_ITEM_SIZE
                    DebugLogger.trace(
                        f"Item '{item_id}' missing size/scale, auto-setting to {self.DEFAULT_ITEM_SIZE}",
                        category="item"
                    )

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
        get_events().subscribe(EnemyDiedEvent, self.on_enemy_died)

    def _load_fallback_image(self) -> None:
        """Load fallback dummy_item image."""
        fallback_path = "assets/images/null.png"
        if os.path.exists(fallback_path):
            try:
                self._fallback_image = pygame.image.load(fallback_path).convert_alpha()
                DebugLogger.init_sub(f"Loaded fallback image")
            except Exception as e:
                DebugLogger.warn(f"Failed loading fallback: {e}")

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
        asset_filename = item_data.get("asset_path")
        if asset_filename:
            full_path = os.path.join(self.ASSET_BASE_PATH, asset_filename)
            image = self._load_item_image(item_id.value, full_path)

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
        """Load item sprite with fallback support."""

        if asset_path in self._image_cache:
            return self._image_cache[asset_path]

        item_data = self._item_definitions.get(item_id, {})
        size = item_data.get("size")

        if os.path.exists(asset_path):
            try:
                img = pygame.image.load(asset_path).convert_alpha()

                # Do NOT scale here. Raw sprite only.
                self._image_cache[asset_path] = img
                return img
            except Exception as e:
                DebugLogger.warn(f"Failed loading {asset_path}: {e}")

        # Use fallback
        if self._fallback_image:
            img = self._fallback_image.copy()
            if size:
                return pygame.transform.scale(img, tuple(size))
            return img

        return None
