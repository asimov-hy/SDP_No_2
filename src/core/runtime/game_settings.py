"""
game_settings.py
----------------
Centralized constants for all game systems.
"""


# ===========================================================
# Display & Performance
# ===========================================================

class Display:
    """Screen and window configuration."""
    WIDTH: int = 1280
    HEIGHT: int = 720
    FPS: int = 60
    CAPTION: str = "202X"

    WINDOW_SIZES = {
        "small": (1280, 720),
        "medium": (1920, 1080),
        "large": (2560, 1440),
    }
    DEFAULT_WINDOW_SIZE: str = "small"


# ===========================================================
# Physics & Timing
# ===========================================================

class Physics:
    """Physics and update timing."""
    UPDATE_RATE: int = 60
    FIXED_DT: float = 1 / UPDATE_RATE
    MAX_FRAME_TIME: float = 0.1


# ===========================================================
# Bounds & Margins
# ===========================================================

class Bounds:
    """Margin values for entity lifecycle management."""
    # Enemies
    ENEMY_DAMAGE_MARGIN: int = 50
    ENEMY_CLEANUP_MARGIN: int = 200

    # Bullets
    BULLET_PLAYER_MARGIN: int = 50
    BULLET_ENEMY_MARGIN: int = 100

    # Items
    ITEM_CLEANUP_MARGIN: int = 50

    # Environment
    ENV_DAMAGE_MARGIN: int = 0
    ENV_CLEANUP_MARGIN: int = 300


# ===========================================================
# Rendering Layers
# ===========================================================

class Layers:
    """Z-order for rendering."""
    BACKGROUND: int = 0
    ENEMIES: int = 1
    PICKUPS: int = 2
    BULLETS: int = 3
    PLAYER: int = 4
    PARTICLES: int = 5
    UI: int = 9
    DEBUG: int = 150


# ===========================================================
# Player Defaults
# ===========================================================

class Player:
    """Player configuration defaults."""
    SPEED: int = 300
    FOCUSED_SPEED: int = 150
    HITBOX_RADIUS: int = 2


# ===========================================================
# Debug Display
# ===========================================================

class Debug:
    """Visual debug toggles -- not related to logging."""
    SHOW_FPS: bool = True
    FRAME_TIME_WARNING: float = 16.67
    HITBOX_VISIBLE: bool = False
    HITBOX_LINE_WIDTH: int = 5