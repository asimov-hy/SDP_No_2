"""
Scene module exports.

Provides base scene class, states, and transition utilities.
"""

from src.scenes.base_scene import BaseScene
from src.scenes.scene_state import SceneState
from src.scenes.transitions import (
    BaseTransition,
    FadeTransition,
    UIFadeOverlay,
    UISlideAnimation,
)

__all__ = [
    # Core
    'BaseScene',
    'SceneState',
    # Transitions
    'BaseTransition',
    'FadeTransition',
    'UIFadeOverlay',
    'UISlideAnimation',
]