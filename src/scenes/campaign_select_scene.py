"""
campaign_select_scene.py
------------------------
Campaign/mission selection screen with dynamic level loading.
"""

from src.scenes.base_scene import BaseScene
from src.systems.level.level_registry import LevelRegistry
from src.core.debug.debug_logger import DebugLogger


class CampaignSelectScene(BaseScene):
    """Campaign selection scene with dynamic level list."""

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "ui"
        self.ui = services.ui_manager
        self.selected_campaign = None

    def on_enter(self):
        """Load campaign list when entering."""
        self.ui.load_screen("campaign_select", "screens/campaign_select.yaml")
        self._populate_campaign_list()
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

        # Check for campaign selection (format: "campaign:campaign_name")
        if action and action.startswith("campaign:"):
            campaign_name = action.split(":", 1)[1]
            self.selected_campaign = campaign_name
            DebugLogger.state(f"Selected campaign: {campaign_name}")
            self.scene_manager.set_scene("Game", campaign_name=campaign_name)
        elif action == "back":
            self.scene_manager.set_scene("MainMenu")

    def _populate_campaign_list(self):
        """Dynamically populate campaign list from registry."""
        # Get screen root
        screen = self.ui.screens.get("campaign_select")
        if not screen:
            DebugLogger.warn("Campaign select screen not found")
            return

        # Find campaign_list container by ID
        container = self._find_element_by_id(screen, "campaign_list")
        if not container:
            DebugLogger.warn("Campaign list container not found")
            return

        # Clear existing children
        container.children.clear()

        # Get all campaigns from registry
        campaign_names = LevelRegistry.list_campaigns()

        if not campaign_names:
            DebugLogger.warn("No campaigns found in registry")
            # Add placeholder message
            self._add_no_campaigns_message(container)
            return

        # Create button for each campaign
        for campaign_name in campaign_names:
            campaign_levels = LevelRegistry.get_campaign(campaign_name)
            if not campaign_levels:
                continue

            # Get campaign metadata
            campaign_data = LevelRegistry._campaigns.get(campaign_name, {})
            display_name = campaign_data.get("name", campaign_name)
            level_count = len(campaign_levels)

            # Create campaign button
            button_config = {
                "type": "button",
                "text": f"{display_name} ({level_count} levels)",
                "width": 600,
                "height": 60,
                "action": f"campaign:{campaign_name}",
                "font_size": 24,
                "color": [80, 120, 80],
                "border": 2,
                "border_color": [120, 160, 120],
                "border_radius": 8
            }

            button = self.ui.loader.load_from_dict(button_config)
            container.add_child(button)

        DebugLogger.init_sub(f"Populated {len(campaign_names)} campaigns")

    def _find_element_by_id(self, element, target_id):
        """Recursively find element by ID."""
        if element.id == target_id:
            return element

        # Check children if container
        if hasattr(element, 'children'):
            for child in element.children:
                result = self._find_element_by_id(child, target_id)
                if result:
                    return result

        return None

    def _add_no_campaigns_message(self, container):
        """Add message when no campaigns available."""
        label_config = {
            "type": "label",
            "text": "No campaigns available",
            "font_size": 24,
            "color": [150, 150, 150]
        }
        label = self.ui.loader.load_from_dict(label_config)
        container.add_child(label)