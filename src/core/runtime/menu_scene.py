"""
menu_scene.py
-------------
Base class for menu/UI scenes (uses "ui" input context).
"""

from src.core.runtime.base_scene import BaseScene


class MenuScene(BaseScene):
    """Base class for scenes that use UI input (menu navigation, buttons)."""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        self.input_context = "ui"  # Always uses UI bindings