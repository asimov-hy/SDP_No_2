"""
settings_scene.py
-----------------
Settings/options menu - controls, audio, display.
"""

from src.scenes.base_scene import BaseScene


class SettingsScene(BaseScene):
    """Settings menu scene."""

    def __init__(self, services, caller_scene=None):
        super().__init__(services)
        self.input_context = "ui"
        self.caller_scene = caller_scene
        self.ui = services.ui_manager

    def on_load(self, caller=None, **scene_data):
        """Remember which scene opened settings."""
        if caller:
            self.caller_scene = caller

    def on_enter(self):
        """Load settings UI."""
        self.ui.load_screen("settings", "screens/settings.yaml")
        self.ui.show_screen("settings")

    def on_exit(self):
        """Called when leaving scene."""
        self.ui.hide_screen("settings")

    def update(self, dt: float):
        """Update settings UI."""
        mouse_pos = self.input_manager.get_mouse_pos()
        self.ui.update(dt, mouse_pos)

    def draw(self, draw_manager):
        """Render settings menu."""
        self.ui.draw(draw_manager)

    def handle_event(self, event):
        """Handle input events."""
        action = self.ui.handle_event(event)

        if action == "back":
            if self.caller_scene == "Pause":
                # Return to paused game
                self.scene_manager.pop_scene()
            else:
                # Return to main menu
                target = self.caller_scene if self.caller_scene else "MainMenu"
                self.scene_manager.set_scene(target)

        elif action == "toggle_fullscreen":
            # Toggle fullscreen via display manager
            self.display.toggle_fullscreen()

        elif action == "window_size_small":
            self.display.set_window_size("small")

        elif action == "window_size_medium":
            self.display.set_window_size("medium")

        elif action == "window_size_large":
            self.display.set_window_size("large")

        elif action == "apply_settings":
            # Settings are applied immediately, just acknowledge
            from src.core.debug.debug_logger import DebugLogger
            DebugLogger.action("Settings applied")

        elif action == "audio_master":
            # TODO: Implement volume control
            pass