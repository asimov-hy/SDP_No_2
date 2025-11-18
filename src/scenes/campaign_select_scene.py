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

    def on_enter(self):
        """Load campaign list when entering."""
        self.ui.load_screen("campaign_select", "screens/campaign_select.yaml")
        self._update_button_states()
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

    def _update_button_states(self):
        """Update button enabled states based on unlock status."""
        screen = self.ui.screens.get("campaign_select")
        if not screen:
            return

        # Update each level button
        level_ids = ["demo_level", "test_straight", "test_homing"]
        for level_id in level_ids:
            button = self._find_element(screen, f"btn_{level_id}")
            if button:
                level_config = self.level_registry.get(level_id)
                if level_config:
                    button.enabled = level_config.unlocked

    def _find_element(self, element, target_id):
        """Recursively find element by id."""
        if hasattr(element, 'id') and element.id == target_id:
            return element
        if hasattr(element, 'children'):
            for child in element.children:
                result = self._find_element(child, target_id)
                if result:
                    return result
        return None