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

        # TODO: Load UI layout
        # self.ui = services.ui_manager
        # self.ui.load_screen("main_menu")

    def on_enter(self):
        """Called when scene becomes active."""
        pass

    def update(self, dt: float):
        """Update menu logic."""
        # TODO: Update UI
        # self.ui.update(dt, pygame.mouse.get_pos())

        # TEMP: Auto-skip to campaign select for testing
        if self.input_manager.action_pressed("confirm"):
            self.scene_manager.set_scene("CampaignSelect")

    def draw(self, draw_manager):
        """Render menu."""
        # TODO: Draw UI
        # self.ui.draw(draw_manager)

        # TEMP: Placeholder visuals
        surf = pygame.Surface((600, 100))  # Wider surface
        surf.fill((50, 50, 100))

        font = pygame.font.Font(None, 48)
        text = font.render("MAIN MENU - Press SPACE", True, (255, 255, 255))
        surf.blit(text, (50, 30))  # More padding

        draw_manager.queue_draw(surf, surf.get_rect(center=(640, 360)), layer=0)

    def handle_event(self, event):
        """Handle input events."""
        # TODO: Forward to UI
        # self.ui.handle_event(event)
        pass