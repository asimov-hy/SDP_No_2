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
    UPDATE_RATE = 60  # Hz (matches display FPS for simplicity)
    FIXED_DT = 1 / UPDATE_RATE  # 0.01666... seconds
    MAX_FRAME_TIME = 0.1  # Cap at 100ms to prevent death spiral


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
    SPEED = 300  # pixels per second
    FOCUSED_SPEED = 150  # For bullets hell "focus mode" (hold shift)
    HITBOX_RADIUS = 2  # Tiny hitbox for bullets hell fairness


# ===========================================================
# Bullet Configuration - EXAMPLE
# ===========================================================
# class Bullets:
#     PLAYER_SPEED = 400
#     ENEMY_SPEED = 200
#     MAX_COUNT = 1000  # Performance cap
#     POOL_SIZE = 500  # Pre-allocate this many


# ===========================================================
# Enemy Configuration - EXAMPLE
# ===========================================================
# class Enemies:
#     MAX_COUNT = 100
#     POOL_SIZE = 50


# ===========================================================
# Debug Configuration
# ===========================================================
class Debug:
    # Core Flags
    VERBOSE_ENTITY_INIT = False
    VERBOSE_ENTITY_DEATH = False
    TRACE_UPDATES = False
    STAGE_SUMMARY = True
    SHOW_FPS = True
    FRAME_TIME_WARNING = 16.67  # ms (warn if slower than 60 FPS)

    # -----------------------------------------------------------
    # Hitbox Debugging
    # -----------------------------------------------------------
    HITBOX_ACTIVE = True          # Always active for collision checks
    HITBOX_VISIBLE = False        # Visible only in debug mode
    VERBOSE_HITBOX_UPDATE = False
    VERBOSE_HITBOX_DRAW = False

    HITBOX_LINE_WIDTH = 5
