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
            "music_volume": 100,
            "bfx_volume": 100,
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

        # 1. Start with defaults
        merged_settings = copy.deepcopy(self.DEFAULTS)

        # 2. Load and return defaults if setting file doesn't exist
        if not os.path.exists(self.settings_file):
            DebugLogger.system("Using default settings")
            return merged_settings

        try:
            with open(self.settings_file, 'r') as f:
                loaded = json.load(f)
            self._merge_recursive(merged_settings, loaded)
            DebugLogger.system(f"Loaded user settings from {self.settings_file}")

        except (json.JSONDecodeError, IOError, OSError) as e:
            DebugLogger.warn(f"Failed to load settings: {e}")
            return copy.deepcopy(self.DEFAULTS)

        return merged_settings

    def _merge_recursive(self, base, update):
        """
        Recursively merge 'update' dict into 'base' dict.
        Allows partial updates (e.g., only changing volume).
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._merge_recursive(base[key], value)
            else:
                base[key] = value


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