"""
mission_select_scene.py
------------------------
Campaign/mission selection screen.
"""

from src.scenes.base_scene import BaseScene
from src.scenes.transitions.transitions import FadeTransition


class MissionSelectScene(BaseScene):
    """Mission selection scene."""

    BACKGROUND_CONFIG = {
        "layers": [{
            "image": "assets/images/maps/mission_select.png",
            "scroll_speed": [1, 0],
            "parallax": [0, 0]
        }]
    }

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "ui"
        self.ui = services.ui_manager
        self.level_registry = services.get_global("level_registry")
        self.current_campaign = "main"

    def on_enter(self):
        """Load campaign list when entering."""
        self._setup_background(self.BACKGROUND_CONFIG)

        self.ui.load_screen("level_select", "screens/level_select.yaml")
        self._populate_levels()
        self.ui.show_screen("level_select")

    def on_exit(self):
        """Called when leaving scene."""
        self._clear_background()

        self.ui.hide_screen("level_select")

    def update(self, dt: float):
        """Update selection logic."""
        self._update_background(dt)

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
            self.scene_manager.set_scene("Game", transition=FadeTransition(0.5), level_id=level_id)

        elif action == "back":
            self.scene_manager.set_scene("MainMenu", transition=FadeTransition(0.3))

    def _populate_levels(self):
        """Update level button text dynamically."""
        all_levels = self.level_registry.get_campaign(self.current_campaign)

        # Update the 3 static level buttons
        for i in range(3):
            button_id = f"level_btn_{i}"
            button = self.ui.find_element_by_id("level_select", button_id)

            if button and i < len(all_levels):
                level = all_levels[i]
                # Update button text and action
                button.text = level.name
                button.action = f'select_level_{level.id}'
                button.enabled = level.unlocked

                # Visual feedback for locked missions
                if not level.unlocked:
                    button.color = (80, 80, 80)
                    button.border_color = (120, 120, 120)
                else:
                    button.color = (60, 100, 180)
                    button.border_color = (100, 140, 220)

                button.mark_dirty()
            elif button:
                # Hide button if no level exists for this slot
                button.visible = False
