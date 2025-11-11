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
        # Core Systems
        "system": True,  # Engine boot, config, and lifecycle events
        "stage": True,  # StageManager / wave progression
        "animation": True,  # Animation initialization and updates
        "base_entity_logic": True,  # Entity base behavior and shared logic

        # Gameplay Systems
        "collision": False,  # CollisionManager (hit detection, tracing)
        "effects": False,  # Destruction, particle, and impact effects
        "entity_spawning": False,  # Entity creation events
        "entity_cleanup": False,  # Entity removal / recycling logs
        "drawing": False,  # DrawManager / render operations

        # Input & User Actions
        "user_action": False  # Player input, controls, and UI actions
    }

    # Output Style
    SHOW_TIMESTAMP = True
    SHOW_CATEGORY = True
    SHOW_LEVEL = True
    # Optional: SAVE_TO_FILE = False
