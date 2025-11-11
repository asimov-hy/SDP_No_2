"""
debug_logger.py
---------------
Lightweight console logger for consistent, colorized, source-tagged engine output.

Responsibilities
----------------
- Provide uniform, readable log formatting across modules.
- Distinguish between system, state, action, and warning logs.
- Include timestamps and source identifiers in all messages.
"""

import inspect
from datetime import datetime
import os
from src.core.game_settings import LoggerConfig


class DebugLogger:
    """Global logger with consistent, colorized, source-tagged output."""

    COLORS = {
        "reset":  "\033[0m",

        "init": "\033[97m",  # Bright white
        "system": "\033[95m",  # Magenta

        "action": "\033[92m",  # Green
        "state": "\033[96m",  # Cyan
        "warn": "\033[93m",  # Yellow

        "trace": "\033[94m",    # Blue
    }

    # ===========================================================
    # Internal Helpers
    # ===========================================================
    @staticmethod
    def _get_caller():
        """Detect the class or module where the logger was invoked (not defined)."""
        stack = inspect.stack()

        # Find where this logger was called from (_log or init)
        for i, frame in enumerate(stack):
            if frame.function in ("_log", "init"):
                # +2 skips the logger internals (_log → public method → actual caller)
                depth = i + 2
                break
        else:
            depth = 2  # fallback if nothing matches

        frame = stack[depth]
        module = inspect.getmodule(frame[0])

        # Inside a class method
        if "self" in frame.frame.f_locals:
            return frame.frame.f_locals["self"].__class__.__name__

        # Inside a classmethod
        if "cls" in frame.frame.f_locals:
            return frame.frame.f_locals["cls"].__name__

        # Otherwise, fall back to the filename
        if module and hasattr(module, "__file__"):
            return os.path.splitext(os.path.basename(module.__file__))[0]

        return "Unknown"

    @staticmethod
    def _get_caller_for_init():
        """Detect the class or module where DebugLogger.init() is executed."""
        stack = inspect.stack()

        for i, frame in enumerate(stack):
            if frame.function == "init":
                depth = i + 1  # one frame up -> actual site of init() call
                break
        else:
            depth = 2

        frame = stack[depth]
        module = inspect.getmodule(frame[0])

        if "self" in frame.frame.f_locals:
            return frame.frame.f_locals["self"].__class__.__name__
        if "cls" in frame.frame.f_locals:
            return frame.frame.f_locals["cls"].__name__

        if module and hasattr(module, "__file__"):
            return os.path.splitext(os.path.basename(module.__file__))[0]
        return "Unknown"

    # ===========================================================
    # Logger Filtering
    # ===========================================================
    @staticmethod
    def _should_log(category: str, level: str) -> bool:
        """Check if this log type and category should print."""
        if not LoggerConfig.ENABLE_LOGGING:
            return False

        # Category check
        if category not in LoggerConfig.CATEGORIES:
            return False
        if not LoggerConfig.CATEGORIES[category]:
            return False

        # Level check
        order = ["NONE", "ERROR", "WARN", "INFO", "VERBOSE"]
        if order.index(level) > order.index(LoggerConfig.LOG_LEVEL):
            return False

        return True

    # ===========================================================
    # Core Logging Utility
    # ===========================================================
    @staticmethod
    def _log(tag: str, message: str, color: str = "reset",
             category: str = "system", level: str = "INFO",
             meta_mode: str = "full", sub: int = 0):
        """
        Core log formatter with filtering, indentation, and metadata display.

        Args:
            tag (str): Log tag (e.g., SYSTEM, STATE).
            message (str): Message text.
            color (str): Terminal color key.
            category (str): Log category for filtering.
            level (str): Log level (INFO, WARN, etc.).
            meta_mode (str): Metadata mode ("full", "time", "simple", "none").
            sub (int): Indentation level for hierarchical logs.
        """
        if not DebugLogger._should_log(category, level):
            return

        color_code = DebugLogger.COLORS.get(color, DebugLogger.COLORS["reset"])
        reset = DebugLogger.COLORS["reset"]

        # Indentation and branch marker
        indent = ""
        if sub > 0:
            indent = " " * (4 * sub) + "└─ "

        timestamp = datetime.now().strftime("%H:%M:%S")
        source = DebugLogger._get_caller()

        # Select metadata prefix
        if meta_mode == "full":
            prefix = f"[{timestamp}] [{source}][{tag}] "
        elif meta_mode == "time":
            prefix = f"[{timestamp}] "
        elif meta_mode == "file":
            prefix = f"[{tag}] "
        else:  # "none"
            prefix = ""

        print(f"{color_code}{indent}{prefix}{message}{reset}")

    # ===========================================================
    # Public Helper Methods
    # ===========================================================
    @staticmethod
    def action(msg: str, category: str = "system", meta_mode: str = "full", sub: int = 0):
        DebugLogger._log("ACTION", msg, "action", category, "INFO", meta_mode, sub)

    @staticmethod
    def state(msg: str, category: str = "system", meta_mode: str = "full", sub: int = 0):
        DebugLogger._log("STATE", msg, "state", category, "INFO", meta_mode, sub)

    @staticmethod
    def system(msg: str, category: str = "system", meta_mode: str = "full", sub: int = 0):
        DebugLogger._log("SYSTEM", msg, "system", category, "INFO", meta_mode, sub)

    @staticmethod
    def warn(msg: str, category: str = "system", meta_mode: str = "full", sub: int = 0):
        DebugLogger._log("WARN", msg, "warn", category, "WARN", meta_mode, sub)

    @staticmethod
    def trace(msg: str, category: str = "collision", meta_mode: str = "full", sub: int = 0):
        DebugLogger._log("TRACE", msg, "trace", category, "VERBOSE", meta_mode, sub)

    @staticmethod
    def init(msg: str = "", color: str = "init",
             meta_mode: str = "full", category: str = "system", sub: int = 0):
        """Initialization log with sub-level and metadata control."""
        if not DebugLogger._should_log(category, "INFO"):
            return

        color_code = DebugLogger.COLORS.get(color, DebugLogger.COLORS["init"])
        reset = DebugLogger.COLORS["reset"]

        if not msg.strip():
            print()
            return

        indent = ""
        if sub > 0:
            indent = " " * (4 * sub) + "└─ "

        timestamp = datetime.now().strftime("%H:%M:%S")
        source = DebugLogger._get_caller_for_init()

        # Select metadata prefix
        if meta_mode == "full":
            prefix = f"[{timestamp}] [{source}][INIT] "
        elif meta_mode == "time":
            prefix = f"[{timestamp}] "
        elif meta_mode == "simple":
            prefix = "[INIT] "
        else:
            prefix = ""

        print(f"{color_code}{indent}{prefix}{msg}{reset}")
