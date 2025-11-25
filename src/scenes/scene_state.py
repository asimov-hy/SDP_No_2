"""
scene_state.py
--------------
Defines the lifecycle states a scene can be in.
"""

from enum import Enum


class SceneState(Enum):
    """Lifecycle states for scene management."""
    INACTIVE = "inactive"       # Not loaded
    LOADING = "loading"         # Currently loading resources
    ACTIVE = "active"           # Running normally
    PAUSED = "paused"           # Frozen for pause menu
    EXITING = "exiting"         # Cleaning up before transition
    TRANSITIONING = "transitioning"  # Playing transition animation
