# Screen and game constants
GAME_WIDTH = 1280
GAME_HEIGHT = 720
# backward compatibility
SCREEN_WIDTH = GAME_WIDTH
SCREEN_HEIGHT = GAME_HEIGHT

FPS = 60

# Player settings
PLAYER_SPEED = 300  # pixels per second
# ===========================================================
# Global Runtime References
# ===========================================================
GLOBAL_PLAYER = None

class DebugConfig:
    VERBOSE_ENTITY_INIT = False
    VERBOSE_ENTITY_DEATH = False
    TRACE_UPDATES = False
    STAGE_SUMMARY = True