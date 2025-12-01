"""
Entity management system exports.

Provides managers for spawning, pooling, and tracking game entities.
"""

from src.systems.entity_management.entity_registry import EntityRegistry
from src.systems.entity_management.spawn_manager import SpawnManager
from src.systems.entity_management.bullet_manager import BulletManager
from src.systems.entity_management.item_manager import ItemManager

__all__ = [
    'EntityRegistry',
    'SpawnManager',
    'BulletManager',
    'ItemManager',
]