"""
ui_controller.py
----------------
Handles HUD, pause menu, and UI management.
Developer D's responsibility.
"""

import pygame
from src.core.runtime.scene_controller import SceneController


class UIController(SceneController):
    """Manages UI, HUD, and pause menu."""

    def __init__(self, scene):
        super().__init__(scene)
        self.ui = scene.ui

    def update(self, dt: float):
        """Update UI elements."""
        self.ui.update(dt, pygame.mouse.get_pos())

    def draw(self, draw_manager):
        """Render UI elements."""
        self.ui.draw(draw_manager)

    def handle_event(self, event):
        """Forward events to UI system."""
        self.ui.handle_event(event)

    def on_pause(self):
        """Show pause menu when game pauses."""
        self.ui.show_screen("pause")

    def on_resume(self):
        """Hide pause menu when game resumes."""
        self.ui.hide_screen("pause")