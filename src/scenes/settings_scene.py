"""
settings_scene.py
-----------------
Settings/options menu - controls, audio, display.
"""

from src.scenes.base_scene import BaseScene
from src.scenes.transitions.transitions import FadeTransition
from src.audio.sound_manager import get_sound_manager


class SettingsScene(BaseScene):
    """Settings menu scene."""

    BACKGROUNDS_PATH = "assets/images/backgrounds/"

    BACKGROUND_CONFIG = {
        "layers": [{
            "image": BACKGROUNDS_PATH + "settings_menu.png",
            "scroll_speed": [0, 0],
            "parallax": [0, 0]
        }]
    }

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
        self._setup_background(self.BACKGROUND_CONFIG)

        self.ui.load_screen("settings", "screens/settings.yaml")
        self.ui.show_screen("settings")

        self.refresh_volume_labels()

    def on_exit(self):
        """Called when leaving scene."""
        self._clear_background()

        self.ui.hide_screen("settings")

    def update(self, dt: float):
        """Update settings UI."""
        self._update_background(dt)

        # ESC key to go back
        if self.input_manager.action_pressed("back"):
            if self.caller_scene == "Pause":
                self.scene_manager.pop_scene()
            else:
                self.scene_manager.set_scene("MainMenu", transition=FadeTransition(0.3))
            return

        mouse_pos = self.input_manager.get_effective_mouse_pos()
        self.ui.update(dt, mouse_pos)

    def draw(self, draw_manager):
        """Render settings menu."""
        self.ui.draw(draw_manager)

    def handle_event(self, event):
        """Handle input events."""
        action = self.ui.handle_event(event)

        if action:
            # List of actions that change volume level
            volume_actions = [
                "master_vol_down", "master_vol_up",
                "bgm_vol_down", "bgm_vol_up",
                "bfx_vol_down", "bfx_vol_up"
            ]

            if action in volume_actions:
                self.handle_ui_action(action)

            elif action == "back":
                if self.caller_scene == "Pause":
                    # Return to paused game
                    self.scene_manager.pop_scene()
                else:
                    # Return to main menu
                    target = self.caller_scene if self.caller_scene else "MainMenu"
                    self.scene_manager.set_scene("MainMenu", transition=FadeTransition(0.3))

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

    def handle_ui_action(self, action_id,):
        sound_manager = get_sound_manager()
        step = 10

        # Master Volume
        if "master" in action_id:
            current_vol = sound_manager.get_master_volume_level()

            if action_id == "master_vol_down":
                sound_manager.set_master_volume(max(0, current_vol - step))
            elif action_id == "master_vol_up":
                sound_manager.set_master_volume(min(100, current_vol + step))

            # Update volume label
            label = self.ui.find_element_by_id("settings", "volume_value_label")
            if label:
                label.set_text(f"{sound_manager.get_master_volume_level()}%")

        # BGM Volume
        elif "bgm" in action_id:
            current_vol = sound_manager.get_bgm_level()

            if action_id == "bgm_vol_down":
                sound_manager.set_bgm_volume(max(0, current_vol - step))
            elif action_id == "bgm_vol_up":
                sound_manager.set_bgm_volume(min(100, current_vol + step))

            label = self.ui.find_element_by_id("settings", "bgm_volume_value_label")
            if label:
                label.set_text(f"{sound_manager.get_bgm_level()}%")

        # BFX Volume
        elif "bfx" in action_id:
            current_vol = sound_manager.get_bfx_level()

            if action_id == "bfx_vol_down":
                sound_manager.set_bfx_volume(max(0, current_vol - step))
            elif action_id == "bfx_vol_up":
                sound_manager.set_bfx_volume(min(100, current_vol + step))

            label = self.ui.find_element_by_id("settings", "bfx_volume_value_label")
            if label:
                label.set_text(f"{sound_manager.get_bfx_level()}%")

    def on_settings_open(self, ui_elements):
        current_vol = get_sound_manager().get_master_level()
        ui_elements["volume_value_label"].set_text(f"{current_vol}%")

    def refresh_volume_labels(self):
        sm = get_sound_manager()

        lbl_master = self.ui.find_element_by_id("settings", "volume_value_label")
        lbl_bgm = self.ui.find_element_by_id("settings", "bgm_volume_value_label")
        lbl_bfx = self.ui.find_element_by_id("settings", "bfx_volume_value_label")

        # 요소가 존재하면 텍스트 업데이트 (set_text 메서드 사용)
        if lbl_master:
            lbl_master.set_text(f"{sm.get_master_volume_level()}%")

        if lbl_bgm:
            lbl_bgm.set_text(f"{sm.get_bgm_level()}%")

        if lbl_bfx:
            lbl_bfx.set_text(f"{sm.get_bfx_level()}%")