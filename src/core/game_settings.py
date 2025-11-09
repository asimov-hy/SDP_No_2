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


# ===========================================================
# Physics & Timing
# ===========================================================
class Physics:
    UPDATE_RATE = 60  # Hz
    FIXED_DT = 1 / UPDATE_RATE
    MAX_FRAME_TIME = 0.1  # Prevent frame spiral


# ===========================================================
# Rendering Layers
# ===========================================================
class Layers:
    BACKGROUND = 0
    ENEMIES = 1
    BULLETS = 2
    PLAYER = 3
    PARTICLES = 4
    EFFECTS = 5
    DEBUG = 9
    UI = 10  # Always on top


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


# ===========================================================
# Logger Configuration (Textual / Console Logging)
# ===========================================================
class LoggerConfig:
    """
    Controls which subsystems emit log messages and at what verbosity level.
    Used by DebugLogger to decide what to print.
    """

    # Master Control
    ENABLE_LOGGING = True
    LOG_LEVEL = "INFO"  # NONE, ERROR, WARN, INFO, VERBOSE

    # Category Filters (only current categories in use)
    CATEGORIES = {
        "system": True,       # Core engine and scene transitions
        "stage": True,        # LevelManager / wave progression logs
        "collision": False,   # CollisionManager (hit detection)
        "effects": False,     # Destruction / VFX / bullet impacts
        "entity_spawning": False,
        "entity_cleanup": False,
    }

    # Output Style
    SHOW_TIMESTAMP = True
    SHOW_CATEGORY = True
    SHOW_LEVEL = True
    # Optional: SAVE_TO_FILE = False
