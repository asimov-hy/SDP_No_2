"""
gameplay_scene.py
-----------------
Base class for gameplay scenes (uses "gameplay" input context).
"""

from src.core.runtime.base_scene import BaseScene


class GameplayScene(BaseScene):
    """Base class for scenes that use gameplay input (player movement, shooting)."""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self.input_context = "gameplay"  # Always uses gameplay bindings