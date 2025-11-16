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


# ===========================================================
# Logger Configuration (Textual / Console Logging)
# ===========================================================
class LoggerConfig:
    """
    Controls which components emit log messages and at what verbosity level.
    Used by DebugLogger to decide what to print.
    """

    # Master Control
    ENABLE_LOGGING = True
    LOG_LEVEL = "INFO"  # NONE, ERROR, WARN, INFO, VERBOSE

    # Category Filters (only current categories in use)
    CATEGORIES = {
        # ---------------------------------------------------
        # Core Engine Systems
        # ---------------------------------------------------
        "loading": False,
        "system": True,              # General runtime lifecycle and initialization
        "display": True,             # DisplayManager, window creation, scaling
        "scene": True,               # SceneManager, transitions, and active scene info
        "input": True,               # InputManager events and key handling
        "debug_hud": True,           # DebugHUD and HUD rendering

        # ---------------------------------------------------
        # Game Loop / State
        # ---------------------------------------------------
        "stage": True,               # StageManager, wave control, scene flow
        "game_state": True,          # GameState transitions and mode tracking
        "timing": False,             # Delta time, fixed step timing, frame stats

        # ---------------------------------------------------
        # Entity & Gameplay Systems
        # ---------------------------------------------------
        "entity_core": True,         # BaseEntity initialization, IDs, and registration
        "entity_logic": True,        # Common entity behavior and updates
        "entity_spawn": False,       # SpawnManager activity and enemy waves
        "entity_cleanup": False,     # Entity removal or offscreen cleanup
        "collision": False,          # CollisionManager, hit detection traces
        "bullet": True,              # BulletManager creation and pooling
        "animation_effects": False,            # Visual/particle effects creation and cleanup
        "animation": True,           # AnimationManager initialization and updates
        "event": True,
        "item": True,
        "level": False,
        "exp": True,

        # ---------------------------------------------------
        # Rendering & Drawing
        # ---------------------------------------------------
        "drawing": False,             # DrawManager operations and layer sorting
        "render": True,              # Display render pipeline and scaling logs

        # ---------------------------------------------------
        # User / Interaction
        # ---------------------------------------------------
        "user_action": False,        # Player input, ui interactions
        "ui": True,                  # UIManager, button states, and transitions

        # ---------------------------------------------------
        # Optional / Experimental
        # ---------------------------------------------------
        "performance": False,        # FPS / frame time diagnostics
        "audio": False               # SoundManager (placeholder)
    }

    # Output Style
    SHOW_TIMESTAMP = True
    SHOW_CATEGORY = True
    SHOW_LEVEL = True
    # Optional: SAVE_TO_FILE = False
