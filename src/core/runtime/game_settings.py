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
# Font Configuration
# ===========================================================

class Fonts:
    DIR: str = "assets/fonts"
    DEFAULT: str = "ScienceGothic_Condensed-Light.ttf"
    FALLBACK: str = None


# ===========================================================
# Physics & Timing
# ===========================================================

class Physics:
    """Physics and update timing."""
    UPDATE_RATE: int = 60
    FIXED_DT: float = 1 / UPDATE_RATE
    MAX_FRAME_TIME: float = 0.1


# ===========================================================
# Input Configuration
# ===========================================================

class Input:
    """Controller and input configuration."""
    CONTROLLER_DEADZONE: float = 0.2
    CONTROLLER_UI_THRESHOLD: float = 0.5


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
    PICKUPS: int = 100
    BULLETS: int = 200
    ENEMIES: int = 300
    PLAYER: int = 400
    PARTICLES: int = 500
    UI: int = 600
    OVERLAY: int = 700      # Pause, game over screens
    MODAL: int = 800    # Tint overlays (if used separately)
    DEBUG: int = 900


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
    PROFILING_ENABLED: bool = False
