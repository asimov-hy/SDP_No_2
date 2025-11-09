"""
player_config.py
----------------
Handles player configuration loading with default fallbacks.

This ensures the player always spawns even if player_config.json
is missing or incomplete.
"""

from src.core.utils.config_manager import load_json

# ===========================================================
# Default Fallback Configuration
# ===========================================================
DEFAULT_CONFIG = {
    # -----------------------------------------------------------
    # Core Player Attributes
    # -----------------------------------------------------------
    "core_attributes": {
        "scale": 1.0,            # Sprite scaling factor
        "speed": 300,            # Base movement speed (pixels/sec)
        "health": 3,             # Starting player health
        "invincible": False,     # Initial invulnerability state
        "hitbox_scale": 0.85,    # Fraction of sprite size for collision box
    },

    # -----------------------------------------------------------
    # Rendering Mode & Default Visuals
    # -----------------------------------------------------------
    "render_mode": "shape",      # "image" or "shape"
    "default_state": {
        "shape_type": "rect",
        "color": (255, 255, 255),
        "size": (32, 32),
        "sprite_path": None,
    },

    # -----------------------------------------------------------
    # Dynamic Visual States
    # -----------------------------------------------------------
    "health_thresholds": {  # Health values where appearance changes
        "moderate": 2,
        "critical": 1,
    },

    "image_states": {            # Sprite variations by damage level
        "normal": "assets/images/player.png",
        "damaged_moderate": "assets/images/player_damaged1.png",
        "damaged_critical": "assets/images/player_damaged2.png",
    },

    "color_states": {            # Color variations by damage level
        "normal": [255, 255, 255],
        "damaged_moderate": [255, 160, 120],
        "damaged_critical": [180, 30, 30]
    },
}


# ===========================================================
# Load JSON + Apply Fallbacks
# ===========================================================
def load_player_config():
    """
    Load player_config.json and apply fallback defaults for missing fields.

    Returns:
        dict: Complete player configuration dictionary.
    """
    config = load_json("player_config.json", {})

    # Fill in any missing keys from defaults
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value
    return config


# ===========================================================
# Global Config Object
# ===========================================================
PLAYER_CONFIG = load_player_config()
