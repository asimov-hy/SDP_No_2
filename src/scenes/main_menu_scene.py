"""
main_menu_scene.py
------------------
Main menu - title, start game, settings, quit.
"""

import pygame
from src.scenes.base_scene import BaseScene


class MainMenuScene(BaseScene):
    """Main menu scene with navigation."""

    BACKGROUND_CONFIG = {
        "layers": [{
            "image": "assets/images/maps/main_menu.png",
            "scroll_speed": [0, 0],
            "parallax": [0, 0]
        }]
    }

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "ui"
        self.ui = services.ui_manager

    def on_enter(self):
        """Called when scene becomes active."""
        self._setup_background(self.BACKGROUND_CONFIG)

        self.ui.clear_hud()
        self.ui.hide_all_screens()
        self.ui.load_screen("main_menu", "screens/main_menu.yaml")
        self.ui.show_screen("main_menu")
        menu_sound = self.services.get_global("sound_manager")
        menu_sound.play_bgm("menu_bgm", loop=-1)

    def on_exit(self):
        """Called when leaving scene."""
        self._clear_background()
        self.ui.hide_screen("main_menu")
        menu_sound = self.services.get_global("sound_manager")
        menu_sound.stop_bgm()

    def update(self, dt: float):
        """Update menu logic."""
        self._update_background(dt)

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