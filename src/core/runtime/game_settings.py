"""
game_settings.py
-----------
Centralized configuration for all game systems.
"""


# ===========================================================
# Display & Performance
# ===========================================================
class Display:
    WIDTH = 1280
    HEIGHT = 720
    FPS = 60
    CAPTION = "202X"

    # Window size presets
    WINDOW_SIZES = {
        "small": (1280, 720),  # 1x - 720p
        "medium": (1920, 1080),  # 1.5x - 1080p
        "large": (2560, 1440),  # 2x - 1440p
    }
    DEFAULT_WINDOW_SIZE = "small"


# ===========================================================
# Physics & Timing
# ===========================================================
class Physics:
    UPDATE_RATE = 60  # Hz
    FIXED_DT = 1 / UPDATE_RATE
    MAX_FRAME_TIME = 0.1  # Prevent frame spiral


class Bounds:
    """Margin values for entity lifecycle management"""
    # Enemies
    ENEMY_DAMAGE_MARGIN = 50  # Must enter screen this far to be hittable
    ENEMY_CLEANUP_MARGIN = 200  # Auto-cleanup when this far offscreen

    # Bullets
    BULLET_PLAYER_MARGIN = 50  # Player bullets travel slightly offscreen
    BULLET_ENEMY_MARGIN = 100  # Enemy bullets travel further

    # Items
    ITEM_CLEANUP_MARGIN = 50

    # Environment entities (for future use)
    ENV_DAMAGE_MARGIN = 0  # Hittable immediately
    ENV_CLEANUP_MARGIN = 300


# ===========================================================
# Rendering Layers
# ===========================================================
class Layers:
    BACKGROUND = 0
    ENEMIES = 1
    PICKUPS = 2
    BULLETS = 3
    PLAYER = 4
    PARTICLES = 5
    UI = 9
    DEBUG = 150   # Always on top


# ===========================================================
# Player Configuration
# ===========================================================
class Player:
    SPEED = 300
    FOCUSED_SPEED = 150
    HITBOX_RADIUS = 2


# ===========================================================
# Debug (Visual)
# ===========================================================
class Debug:
    """Visual debug and HUD toggles — not related to logging."""

    SHOW_FPS = True
    FRAME_TIME_WARNING = 16.67
    HITBOX_ACTIVE = True
    HITBOX_VISIBLE = False
    HITBOX_LINE_WIDTH = 5
