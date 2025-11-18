"""
campaign_select_scene.py
------------------------
Campaign/mission selection screen.
"""

from src.scenes.base_scene import BaseScene


class CampaignSelectScene(BaseScene):
    """Campaign selection scene."""

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "ui"
        self.ui = services.ui_manager

    def on_enter(self):
        """Load campaign list when entering."""
        self.ui.load_screen("campaign_select", "screens/campaign_select.yaml")
        self.ui.show_screen("campaign_select")

    def on_exit(self):
        """Called when leaving scene."""
        self.ui.hide_screen("campaign_select")

    def update(self, dt: float):
        """Update selection logic."""
        mouse_pos = self.input_manager.get_mouse_pos()
        self.ui.update(dt, mouse_pos)

    def draw(self, draw_manager):
        """Render campaign list."""
        self.ui.draw(draw_manager)

    def handle_event(self, event):
        """Handle input events."""
        action = self.ui.handle_event(event)

        if action == "start_game":
            self.scene_manager.set_scene("Game")
        elif action == "back":
            self.scene_manager.set_scene("MainMenu")