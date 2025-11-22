"""
debug_logger.py
---------------
Diagnostic console logger with aligned flat report layout.
Keeps meta_mode for normal logs, but renders init reports
in a clean dotted diagnostic style.
"""

import sys
from datetime import datetime

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


black = "\033[0m"
white = "\033[97m"
green = "\033[92m"
magenta = "\033[95m"
cyan = "\033[96m"
blue = "\033[94m"
yellow = "\033[93m"
red = "\033[91m"


class DebugLogger:
    length = 59
    _entry_positions = {}

    COLORS = {
        # Base color
        "reset": black,

        # Initialization / Success
        "init": white,
        "ok": green,

        # System colors
        "system": magenta,
        "state": cyan,
        "action": green,
        "trace": blue,

        # Warnings / Failures
        "warn": yellow,
        "fail": red,
    }

    _LEVEL_VALUES = {"NONE": 0, "ERROR": 1, "WARN": 2, "INFO": 3, "VERBOSE": 4}

    # ===========================================================
    # Internal helpers
    # ===========================================================
    @staticmethod
    def _get_caller():
        """Fast caller detection using direct frame access"""
        try:
            frame = sys._getframe(3)
            if 'self' in frame.f_locals:
                return frame.f_locals['self'].__class__.__name__
            if 'cls' in frame.f_locals:
                return frame.f_locals['cls'].__name__
            return frame.f_code.co_filename.split('/')[-1].replace('.py', '')
        except (ValueError, AttributeError, KeyError):
            return "Unknown"

    @staticmethod
    def _build_prefix(timestamp, source, tag, meta_mode):
        time = f"[{timestamp}]"
        source_ = f"[{source}]"
        tag_ = f"[{tag}]"
        modes = {
            "full":      f"{time} {source_}{tag_} ",
            "no_time":   f"{source_}{tag_} ",
            "no_source": f"{time} {tag_} ",
            "no_tag":    f"{time} {source_} ",
            "time":      f"{time} ",
            "source":    f"{source_} ",
            "tag":       f"{tag_} ",
            "none":      "",
        }
        return modes.get(meta_mode, modes["full"])

    # ===========================================================
    # Core logging
    # ===========================================================
    @staticmethod
    def _should_log(category: str, level: str) -> bool:
        if not LoggerConfig.ENABLE_LOGGING:
            return False
        if not LoggerConfig.CATEGORIES.get(category, False):
            return False
        level_val = DebugLogger._LEVEL_VALUES.get(level, 3)
        config_val = DebugLogger._LEVEL_VALUES.get(LoggerConfig.LOG_LEVEL, 3)
        return level_val <= config_val

    @staticmethod
    def _log(tag: str, message: str, color: str = "reset",
             category: str = "system", level: str = "INFO",
             meta_mode: str = "full"):
        if not DebugLogger._should_log(category, level):
            return
        color_code = DebugLogger.COLORS.get(color, DebugLogger.COLORS["reset"])
        reset = DebugLogger.COLORS["reset"]
        timestamp = datetime.now().strftime("%H:%M:%S")
        source = DebugLogger._get_caller()
        prefix = DebugLogger._build_prefix(timestamp, source, tag, meta_mode)
        print(f"{color_code}{prefix}{message}{reset}")

    # ===========================================================
    # Section layout
    # ===========================================================
    @staticmethod
    def section(title: str, only_title: bool = False):
        """
        Print a centered section block and remember its cursor position for updating.
        """
        color = DebugLogger.COLORS["init"]
        reset = DebugLogger.COLORS["reset"]
        line = "─" * DebugLogger.length

        if only_title:
            # Centered plain title with one blank line above (no brackets or borders)
            title_line = title.rjust(DebugLogger.length)
            print(f"\n{color}{title_line}{reset}")
        else:
            # Full bordered section with brackets
            title_line = f"[{title}]".center(DebugLogger.length)
            print(f"\n{color}{line}\n"
                  f"{title_line}\n"
                  # f"{line}{reset}"
                  )

    # ===========================================================
    # Flat diagnostic INIT layout
    # ===========================================================
    @staticmethod
    def _render_entry(module: str, status: str) -> str:
        """Builds a single formatted line with aligned dots and colored status."""
        status_upper = status.upper()
        color_map = {
            "OK": DebugLogger.COLORS["ok"],
            "LOADING": DebugLogger.COLORS["state"],
            "FAIL": DebugLogger.COLORS["fail"],
        }
        color = color_map.get(status_upper, DebugLogger.COLORS["init"])
        reset = DebugLogger.COLORS["reset"]

        total_length = DebugLogger.length
        prefix = f"> {module}"
        status_str = f"[{status}]"
        dot_start_column = 30
        gap_between_dots_and_status = 1
        dots_start = max(dot_start_column - len(prefix), 1)
        dot_count = max(total_length - (len(prefix) + dots_start + gap_between_dots_and_status + len(status_str)), 1)

        base_color = DebugLogger.COLORS["init"]

        return (
            f"{base_color}{prefix}"
            f"{' ' * dots_start}"
            f"{'·' * dot_count}"
            f"{' ' * gap_between_dots_and_status}"
            f"{color}{status_str}{reset}"
        )

    @staticmethod
    def init_entry(module: str, status: str = "OK"):
        """Prints a new dotted diagnostic entry and records its cursor position."""
        line = DebugLogger._render_entry(module, status)
        DebugLogger._entry_positions[module] = len(DebugLogger._entry_positions)
        print(line)

    @staticmethod
    def init_sub(detail: str, level: int = 1):
        """Print bullet-point sub detail with optional nested indentation."""
        color = DebugLogger.COLORS["init"]
        reset = DebugLogger.COLORS["reset"]

        # Each level adds four spaces of indentation
        indent = " " * (level * 4)
        print(f"{indent}• {color}{detail}{reset}")

    # ===========================================================
    # Public Helper Methods
    # ===========================================================

    @staticmethod
    def init(msg: str = "", category: str = "system", meta_mode: str = "full"):
        """Initialization log — same as normal log, but white and allows blank line spacing."""
        if not msg.strip():
            print()
            return
        DebugLogger._log("INIT", msg, "init", category, "INFO", meta_mode)

    @staticmethod
    def system(msg: str, category: str = "system", meta_mode: str = "full"):
        DebugLogger._log("SYSTEM", msg, "system", category, "INFO", meta_mode)

    @staticmethod
    def state(msg: str, category: str = "system", meta_mode: str = "full"):
        DebugLogger._log("STATE", msg, "state", category, "INFO", meta_mode)

    @staticmethod
    def action(msg: str, category: str = "system", meta_mode: str = "full"):
        DebugLogger._log("ACTION", msg, "ok", category, "INFO", meta_mode)

    @staticmethod
    def trace(msg: str, category: str = "collision", meta_mode: str = "full"):
        DebugLogger._log("TRACE", msg, "trace", category, "VERBOSE", meta_mode)

    @staticmethod
    def warn(msg: str, category: str = "system", meta_mode: str = "full"):
        DebugLogger._log("WARN", msg, "warn", category, "WARN", meta_mode)

    @staticmethod
    def fail(msg: str, category: str = "system", meta_mode: str = "full"):
        """Log fatal or failed initialization events in red."""
        DebugLogger._log("FAIL", msg, "fail", category, "ERROR", meta_mode)
