"""
debug_logger.py
---------------
Diagnostic console logger with category filtering and formatted output.
"""

import sys
from datetime import datetime


# ===========================================================
# Logger Configuration
# ===========================================================

class LoggerConfig:
    """Controls which components emit log messages and at what verbosity."""

    ENABLE_LOGGING = True
    LOG_LEVEL = "INFO"  # NONE, ERROR, WARN, INFO, VERBOSE

    CATEGORIES = {
        # Core Engine
        "loading": False,
        "system": True,
        "display": True,
        "scene": True,
        "input": True,
        "debug_hud": True,

        # Game Loop
        "stage": True,
        "game_state": True,
        "timing": False,

        # Entities
        "entity_core": True,
        "entity_logic": True,
        "entity_spawn": True,
        "entity_cleanup": False,
        "collision": True,
        "bullet": False,
        "animation_effects": False,
        "animation": False,
        "event": True,
        "event_manager": False,
        "item": True,
        "level": False,
        "exp": False,

        # Rendering
        "drawing": False,
        "render": True,

        # User
        "user_action": False,
        "ui": True,

        # Optional
        "performance": False,
        "audio": False
    }

    SHOW_TIMESTAMP = True
    SHOW_CATEGORY = True
    SHOW_LEVEL = True


# ===========================================================
# ANSI Colors
# ===========================================================

class Colors:
    """ANSI escape codes for terminal colors."""
    RESET = "\033[0m"
    WHITE = "\033[97m"
    GREEN = "\033[92m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


# ===========================================================
# Debug Logger
# ===========================================================

class DebugLogger:
    """Static logger with category filtering and colored output."""

    LINE_LENGTH = 59

    COLOR_MAP = {
        "reset": Colors.RESET,
        "init": Colors.WHITE,
        "ok": Colors.GREEN,
        "system": Colors.MAGENTA,
        "state": Colors.CYAN,
        "action": Colors.GREEN,
        "trace": Colors.BLUE,
        "warn": Colors.YELLOW,
        "fail": Colors.RED,
    }

    LEVEL_VALUES = {
        "NONE": 0,
        "ERROR": 1,
        "WARN": 2,
        "INFO": 3,
        "VERBOSE": 4
    }

    # ===========================================================
    # Caller Detection
    # ===========================================================

    @staticmethod
    def _get_caller() -> str:
        """Detect calling class or module name via frame inspection."""
        try:
            frame = sys._getframe(3)

            # Case 1: instance method
            if 'self' in frame.f_locals:
                return frame.f_locals['self'].__class__.__name__

            # Case 2: classmethod
            if 'cls' in frame.f_locals:
                return frame.f_locals['cls'].__name__

            # Case 3: fallback to module
            filename = frame.f_code.co_filename.replace("\\", "/").split("/")[-1]
            module_name = filename.replace(".py", "")

            # Convert snake_case to PascalCase for readability
            parts = module_name.split("_")
            return "".join(p.capitalize() for p in parts)

        except (ValueError, AttributeError, KeyError):
            return "Unknown"

    # ===========================================================
    # Core Logging
    # ===========================================================

    @staticmethod
    def _should_log(category: str, level: str) -> bool:
        """Check if message should be logged based on config."""
        if not LoggerConfig.ENABLE_LOGGING:
            return False
        if not LoggerConfig.CATEGORIES.get(category, False):
            return False
        level_val = DebugLogger.LEVEL_VALUES.get(level, 3)
        config_val = DebugLogger.LEVEL_VALUES.get(LoggerConfig.LOG_LEVEL, 3)
        return level_val <= config_val

    @staticmethod
    def _log(tag: str, message: str, color: str = "reset",
             category: str = "system", level: str = "INFO",
             meta_mode: str = "full"):
        """Internal logging method."""
        if not DebugLogger._should_log(category, level):
            return

        color_code = DebugLogger.COLOR_MAP.get(color, Colors.RESET)
        reset = Colors.RESET
        timestamp = datetime.now().strftime("%H:%M:%S")
        source = DebugLogger._get_caller()
        prefix = DebugLogger._build_prefix(timestamp, source, tag, meta_mode)
        print(f"{color_code}{prefix}{message}{reset}")

    @staticmethod
    def _build_prefix(timestamp: str, source: str, tag: str, meta_mode: str) -> str:
        """Build log line prefix based on meta mode."""
        time_str = f"[{timestamp}]"
        source_str = f"[{source}]"
        tag_str = f"[{tag}]"

        modes = {
            "full": f"{time_str} {source_str}{tag_str} ",
            "no_time": f"{source_str}{tag_str} ",
            "no_source": f"{time_str} {tag_str} ",
            "no_tag": f"{time_str} {source_str} ",
            "time": f"{time_str} ",
            "source": f"{source_str} ",
            "tag": f"{tag_str} ",
            "none": "",
        }
        return modes.get(meta_mode, modes["full"])

    # ===========================================================
    # Public Log Methods
    # ===========================================================

    @staticmethod
    def init(msg: str = "", category: str = "system", meta_mode: str = "full"):
        """Initialization log. Empty message prints blank line."""
        if not msg.strip():
            print()
            return
        DebugLogger._log("INIT", msg, "init", category, "INFO", meta_mode)

    @staticmethod
    def system(msg: str, category: str = "system", meta_mode: str = "full"):
        """System-level log."""
        DebugLogger._log("SYSTEM", msg, "system", category, "INFO", meta_mode)

    @staticmethod
    def state(msg: str, category: str = "system", meta_mode: str = "full"):
        """State change log."""
        DebugLogger._log("STATE", msg, "state", category, "INFO", meta_mode)

    @staticmethod
    def action(msg: str, category: str = "system", meta_mode: str = "full"):
        """Action/success log."""
        DebugLogger._log("ACTION", msg, "ok", category, "INFO", meta_mode)

    @staticmethod
    def trace(msg: str, category: str = "collision", meta_mode: str = "full"):
        """Verbose trace log."""
        DebugLogger._log("TRACE", msg, "trace", category, "VERBOSE", meta_mode)

    @staticmethod
    def warn(msg: str, category: str = "system", meta_mode: str = "full"):
        """Warning log."""
        DebugLogger._log("WARN", msg, "warn", category, "WARN", meta_mode)

    @staticmethod
    def fail(msg: str, category: str = "system", meta_mode: str = "full"):
        """Error/failure log."""
        DebugLogger._log("FAIL", msg, "fail", category, "ERROR", meta_mode)

    # ===========================================================
    # Section Formatting
    # ===========================================================

    @staticmethod
    def section(title: str, only_title: bool = False):
        """Print a section header."""
        color = Colors.WHITE
        reset = Colors.RESET
        line = "─" * DebugLogger.LINE_LENGTH

        if only_title:
            title_line = title.rjust(DebugLogger.LINE_LENGTH)
            print(f"\n{color}{title_line}{reset}")
        else:
            title_line = f"[{title}]".center(DebugLogger.LINE_LENGTH)
            print(f"\n{color}{line}\n{title_line}\n")

    # ===========================================================
    # Init Report Formatting
    # ===========================================================

    @staticmethod
    def init_entry(module: str, status: str = "OK"):
        """Print a dotted diagnostic entry."""
        line = DebugLogger._render_entry(module, status)
        print(line)

    @staticmethod
    def init_sub(detail: str, level: int = 1):
        """Print indented sub-detail."""
        color = Colors.WHITE
        reset = Colors.RESET
        indent = " " * (level * 4)
        print(f"{indent}• {color}{detail}{reset}")

    @staticmethod
    def _render_entry(module: str, status: str) -> str:
        """Build formatted status line with dots."""
        status_upper = status.upper()
        color_map = {
            "OK": Colors.GREEN,
            "LOADING": Colors.CYAN,
            "FAIL": Colors.RED,
        }
        color = color_map.get(status_upper, Colors.WHITE)
        reset = Colors.RESET

        prefix = f"> {module}"
        status_str = f"[{status}]"
        dot_start = 30
        gap = 1

        dots_start = max(dot_start - len(prefix), 1)
        dot_count = max(DebugLogger.LINE_LENGTH - (len(prefix) + dots_start + gap + len(status_str)), 1)

        return (
            f"{Colors.WHITE}{prefix}"
            f"{' ' * dots_start}"
            f"{'.' * dot_count}"
            f"{' ' * gap}"
            f"{color}{status_str}{reset}"
        )
