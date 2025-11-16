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

    def on_pause(self):
        """Show pause menu when game pauses."""
        self.ui.show_screen("pause")

    def on_resume(self):
        """Hide pause menu when game resumes."""
        self.ui.hide_screen("pause")

    def handle_event(self, event):
        """Forward events to UI system and handle pause menu actions."""
        import pygame

        # Let UI system handle the event
        self.ui.handle_event(event)

        # Check if pause menu "Resume" button was clicked
        from src.core.runtime.scene_state import SceneState
        if self.scene.state == SceneState.PAUSED:
            # UI system will have already handled button clicks
            # The scene_manager's ESC handler will call resume
            pass