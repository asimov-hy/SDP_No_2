"""
settings_manager.py
-------------------
Global game settings (graphics, audio, controls).
Singleton pattern for application-wide access.
"""

import json
import os
from src.core.debug.debug_logger import DebugLogger


class SettingsManager:
    """Manages persistent user settings."""

    def __init__(self):
        self.settings_file = "settings.json"

        # Default settings
        self.defaults = {
            "graphics": {
                "fps_limit": 60,
                "vsync": True,
                "fullscreen": False,
                "resolution": [1280, 720]
            },
            "audio": {
                "master_volume": 1.0,
                "music_volume": 0.8,
                "sfx_volume": 1.0,
                "muted": False
            },
            "controls": {
                "mouse_sensitivity": 1.0
            }
        }

        # Current settings (loaded from file or defaults)
        self.settings = self._load()

    def _load(self):
        """Load settings from file or use defaults."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                DebugLogger.system(f"Loaded settings from {self.settings_file}")

                # Merge with defaults (in case new settings added)
                return self._merge_with_defaults(loaded)
            except (json.JSONDecodeError, IOError, OSError) as e:
                DebugLogger.warn(f"Failed to load settings: {e}")
                return self.defaults.copy()
        else:
            DebugLogger.system("Using default settings")
            return self.defaults.copy()

    def _merge_with_defaults(self, loaded):
        """Merge loaded settings with defaults."""
        merged = self.defaults.copy()
        for category, values in loaded.items():
            if category in merged:
                merged[category].update(values)
        return merged

    def save(self):
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            DebugLogger.system(f"Saved settings to {self.settings_file}")
        except (IOError, OSError, TypeError) as e:
            DebugLogger.warn(f"Failed to save settings: {e}")

    def get(self, category, key, default=None):
        """Get a setting value."""
        return self.settings.get(category, {}).get(key, default)

    def set(self, category, key, value):
        """Set a setting value."""
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self.defaults.copy()
        DebugLogger.system("Settings reset to defaults")


# Global singleton
_SETTINGS = None

def get_settings() -> SettingsManager:
    """Get or create the settings singleton."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = SettingsManager()
    return _SETTINGS
