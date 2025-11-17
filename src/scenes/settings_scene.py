"""
settings_scene.py
-----------------
Settings/options menu - controls, audio, display.
"""

import pygame
from src.scenes.base_scene import BaseScene


class SettingsScene(BaseScene):
    """Settings menu scene."""

    def __init__(self, services, caller_scene=None):
        super().__init__(services)
        self.input_context = "ui"
        self.caller_scene = caller_scene  # Track where we came from

        # TODO: Load settings UI
        # self.ui = services.ui_manager
        # self.ui.load_screen("settings")

    def on_load(self, caller=None, **scene_data):
        """Remember which scene opened settings."""
        if caller:
            self.caller_scene = caller

    def update(self, dt: float):
        """Update settings UI."""
        # TODO: Update UI

        # Back to caller scene
        if self.input_manager.action_pressed("back"):
            target = self.caller_scene if self.caller_scene else "MainMenu"
            self.scene_manager.set_scene(target)

    def draw(self, draw_manager):
        """Render settings menu."""
        # TEMP: Placeholder
        surf = pygame.Surface((400, 100))
        surf.fill((50, 100, 50))

        font = pygame.font.Font(None, 48)
        text = font.render("SETTINGS - Press ESC", True, (255, 255, 255))
        surf.blit(text, (20, 30))

        draw_manager.queue_draw(surf, surf.get_rect(center=(640, 360)), layer=0)

    def handle_event(self, event):
        """Handle input events."""
        pass