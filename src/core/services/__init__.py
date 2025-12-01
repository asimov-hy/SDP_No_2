"""
Core services exports.

Provides singleton services, event system, and configuration loading.
"""

from src.core.services.config_manager import load_config
from src.core.services.event_manager import (
    get_events,
    BaseEvent,
    EnemyDiedEvent,
    ItemCollectedEvent,
    PlayerHealthEvent,
    FireRateEvent,
    ScreenShakeEvent,
    BulletClearEvent,
    SpawnPauseEvent,
)
from src.core.services.service_locator import ServiceLocator
from src.core.services.input_manager import InputManager
from src.core.services.display_manager import DisplayManager
from src.core.services.scene_manager import SceneManager

__all__ = [
    # Config
    'load_config',
    # Events
    'get_events',
    'BaseEvent',
    'EnemyDiedEvent',
    'ItemCollectedEvent',
    'PlayerHealthEvent',
    'FireRateEvent',
    'ScreenShakeEvent',
    'BulletClearEvent',
    'SpawnPauseEvent',
    # Services
    'ServiceLocator',
    'InputManager',
    'DisplayManager',
    'SceneManager',
]