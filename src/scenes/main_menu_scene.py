"""
main_menu_scene.py
------------------
Main menu - title, start game, settings, quit.
"""

import pygame
from src.scenes.base_scene import BaseScene


class MainMenuScene(BaseScene):
    """Main menu scene with navigation."""

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "ui"
        self.ui = services.ui_manager

    def on_enter(self):
        """Called when scene becomes active."""
        self.ui.load_screen("main_menu", "screens/main_menu.yaml")
        self.ui.show_screen("main_menu")

    def on_exit(self):
        """Called when leaving scene."""
        self.ui.hide_screen("main_menu")

    def update(self, dt: float):
        """Update menu logic."""
        mouse_pos = self.input_manager.get_mouse_pos()
        self.ui.update(dt, mouse_pos)

    def draw(self, draw_manager):
        """Render menu."""
        self.ui.draw(draw_manager)

    def handle_event(self, event):
        """Handle input events."""
        action = self.ui.handle_event(event)

        if action == "start_game":
            self.scene_manager.set_scene("CampaignSelect")
        elif action == "settings":
            self.scene_manager.set_scene("Settings", caller="MainMenu")
        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))