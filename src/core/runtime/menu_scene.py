"""
menu_scene.py
-------------
Base class for menu/UI scenes (uses "ui" input context).
"""

from src.scenes.base_scene import BaseScene


class MenuScene(BaseScene):
    """Base class for scenes that use UI input (menu navigation, buttons)."""

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "ui"  # Always uses UI bindings