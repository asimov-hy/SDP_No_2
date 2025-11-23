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
        self.level_registry = services.get_global("level_registry")
        self.current_campaign = "test"

    def on_enter(self):
        """Load campaign list when entering."""
        self.ui.load_screen("campaign_select", "screens/campaign_select.yaml")
        self._populate_levels()
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

        if action and action.startswith("select_level_"):
            level_id = action.replace("select_level_", "")
            self.scene_manager.set_scene("Game", level_id=level_id)
        elif action == "back":
            self.scene_manager.set_scene("MainMenu")

    def _populate_levels(self):
        """Populate level list."""
        level_container = self.ui.find_element_by_id("campaign_select", "level_list")
        if not level_container:
            return

        level_container.children.clear()

        all_levels = self.level_registry.get_campaign(self.current_campaign)

        from src.ui.elements.button import UIButton
        for level in all_levels:
            button_config = {
                'width': 500,
                'height': 70,
                'text': level.name,
                'action': f'select_level_{level.id}',
                'enabled': level.unlocked,
                'margin_bottom': 10
            }
            button = UIButton(button_config)
            level_container.add_child(button)