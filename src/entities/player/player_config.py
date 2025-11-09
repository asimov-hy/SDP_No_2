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
    "scale": 1.0,          # Sprite scaling factor
    "speed": 300,          # Base movement speed (pixels/sec)
    "health": 3,           # Starting player health
    "invincible": False,   # Initial invulnerability state
    "hitbox_scale": 0.85,  # Fraction of sprite size for collision box
    "render_mode": "shape",  # "image" or "shape" rendering
    "shape_type": "rect",    # Shape used when render_mode == "shape"
    "color": (255, 80, 80),  # Default color for fallback rendering
    "size": (64, 64),        # Default sprite size when no image is used
    "sprite_path": None      # Optional file path to player sprite
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
