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

        # Pagination
        self.current_page = 0
        self.levels_per_page = 5
        self.current_campaign = "test"

    def on_enter(self):
        """Load campaign list when entering."""
        self.ui.load_screen("campaign_select", "screens/campaign_select.yaml")
        self._populate_page()
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
        elif action == "prev_page":
            self.current_page -= 1
            self._populate_page()
        elif action == "next_page":
            self.current_page += 1
            self._populate_page()
        elif action == "back":
            self.scene_manager.set_scene("MainMenu")

    def _populate_page(self):
        """Populate current page of levels."""
        screen = self.ui.screens.get("campaign_select")
        if not screen:
            return

        # Get level container
        level_container = self._find_element(screen, "level_list")
        if not level_container:
            return

        # Clear existing children
        level_container.children.clear()

        # Get all levels for campaign
        all_levels = self.level_registry.get_campaign(self.current_campaign)

        # Calculate pagination
        start_idx = self.current_page * self.levels_per_page
        end_idx = start_idx + self.levels_per_page
        page_levels = all_levels[start_idx:end_idx]

        # Create buttons for visible levels
        from src.ui.elements.button import UIButton
        for level in page_levels:
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

        # Update page indicator
        total_pages = (len(all_levels) + self.levels_per_page - 1) // self.levels_per_page
        page_label = self._find_element(screen, "page_indicator")
        if page_label:
            page_label.text = f"Page {self.current_page + 1} / {total_pages}"

        # Update navigation buttons
        prev_btn = self._find_element(screen, "btn_prev_page")
        next_btn = self._find_element(screen, "btn_next_page")

        if prev_btn:
            prev_btn.enabled = self.current_page > 0
        if next_btn:
            next_btn.enabled = end_idx < len(all_levels)

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