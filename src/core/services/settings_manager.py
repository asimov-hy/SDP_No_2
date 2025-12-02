"""
settings_manager.py
-------------------
Manages persistent user settings (graphics, audio, controls).
Singleton pattern for application-wide access.
"""

import copy
import json
import os
from src.core.debug.debug_logger import DebugLogger


# ===========================================================
# Settings Manager
# ===========================================================

class SettingsManager:
    """Manages persistent user settings with safe defaults."""

    SETTINGS_FILE = "settings.json"

    DEFAULTS = {
        "graphics": {
            "fps_limit": 60,
            "vsync": True,
            "fullscreen": False,
            "resolution": [1280, 720]
        },
        "audio": {
            "master_volume": 100,
            "music_volume": 80,
            "sfx_volume": 100,
            "muted": False
        },
        "controls": {
            "mouse_sensitivity": 1.0
        }
    }

    def __init__(self, settings_file=None):
        """
        Initialize settings manager.

        Args:
            settings_file: Optional custom path for settings file
        """
        self.settings_file = settings_file or self.SETTINGS_FILE
        self.settings = self._load()

    # ===========================================================
    # Public API
    # ===========================================================

    def get(self, category, key, default=None):
        """
        Get a setting value.

        Args:
            category: Settings category (graphics, audio, controls)
            key: Setting key
            default: Fallback if not found

        Returns:
            Setting value or default
        """
        return self.settings.get(category, {}).get(key, default)

    def set(self, category, key, value):
        """
        Set a setting value.

        Args:
            category: Settings category
            key: Setting key
            value: Value to set
        """
        if category not in self.settings:
            self.settings[category] = {}
        self.settings[category][key] = value

    def save(self):
        """Save current settings to file."""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            DebugLogger.system(f"Saved settings to {self.settings_file}")
        except (IOError, OSError, TypeError) as e:
            DebugLogger.warn(f"Failed to save settings: {e}")

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = copy.deepcopy(self.DEFAULTS)
        DebugLogger.system("Settings reset to defaults")

    def reset_category(self, category):
        """
        Reset a single category to defaults.

        Args:
            category: Category to reset
        """
        if category in self.DEFAULTS:
            self.settings[category] = copy.deepcopy(self.DEFAULTS[category])

    # ===========================================================
    # Loading & Merging
    # ===========================================================

    def _load(self):
        """Load settings from file or use defaults."""
        if not os.path.exists(self.settings_file):
            DebugLogger.system("Using default settings")
            return copy.deepcopy(self.DEFAULTS)

        try:
            with open(self.settings_file, 'r') as f:
                loaded = json.load(f)
            DebugLogger.system(f"Loaded settings from {self.settings_file}")
            return self._merge_with_defaults(loaded)

        except (json.JSONDecodeError, IOError, OSError) as e:
            DebugLogger.warn(f"Failed to load settings: {e}")
            return copy.deepcopy(self.DEFAULTS)

    def _merge_with_defaults(self, loaded):
        """
        Merge loaded settings with defaults.
        Defaults provide missing keys, loaded values take priority.
        """
        merged = copy.deepcopy(self.DEFAULTS)

        for category, values in loaded.items():
            if not isinstance(values, dict):
                continue

            if category in merged:
                merged[category].update(values)
            else:
                merged[category] = values

        return merged


# ===========================================================
# Singleton Access
# ===========================================================

_SETTINGS = None


def get_settings() -> SettingsManager:
    """Get or create the settings singleton."""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = SettingsManager()
    return _SETTINGS


def reset_settings():
    """Reset the singleton. Use for testing or full restart."""
    global _SETTINGS
    _SETTINGS = None