"""
Runtime configuration exports.

Provides game-wide constants and settings. All exports are lightweight
class constants with no initialization overhead.
"""

from src.core.runtime.game_settings import (
    Display,
    Layers,
    Debug,
    Fonts,
    Physics,
    Input,
    Bounds,
    Player,
)
from src.core.runtime.session_stats import get_session_stats

__all__ = [
    # Display & Rendering
    'Display',
    'Layers',
    # Configuration
    'Fonts',
    'Physics',
    'Input',
    'Bounds',
    'Player',
    # Debug
    'Debug',
    # Session
    'get_session_stats',
]