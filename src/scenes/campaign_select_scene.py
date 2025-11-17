"""
campaign_select_scene.py
------------------------
Campaign/mission selection screen.
"""

import pygame
from src.scenes.base_scene import BaseScene


class CampaignSelectScene(BaseScene):
    """Campaign selection scene."""

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "ui"

        # TODO: Load available campaigns from LevelRegistry
        self.campaigns = []
        self.selected_idx = 0

    def on_enter(self):
        """Load campaign list when entering."""
        # TODO: Query LevelRegistry for available campaigns
        pass

    def update(self, dt: float):
        """Update selection logic."""
        # TODO: Handle campaign selection

        # TEMP: Auto-start default campaign
        if self.input_manager.action_pressed("confirm"):
            self.scene_manager.set_scene("Game", campaign_name="test")

        # Back to main menu
        if self.input_manager.action_pressed("back"):
            self.scene_manager.set_scene("MainMenu")

    def draw(self, draw_manager):
        """Render campaign list."""
        # TEMP: Placeholder
        surf = pygame.Surface((400, 100))
        surf.fill((100, 50, 50))

        font = pygame.font.Font(None, 48)
        text = font.render("SELECT CAMPAIGN - Press ENTER", True, (255, 255, 255))
        surf.blit(text, (20, 30))

        draw_manager.queue_draw(surf, surf.get_rect(center=(640, 360)), layer=0)

    def handle_event(self, event):
        """Handle input events."""
        pass