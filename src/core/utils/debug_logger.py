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
    # Core Logging Utility
    # ===========================================================
    @staticmethod
    def _log(tag: str, message: str, color: str = "reset"):
        """
        Core log formatter.

        Args:
            tag (str): The type of log message (e.g., SYSTEM, STATE, ACTION, WARN).
            message (str): Descriptive message to display.
            color (str, optional): Color key for terminal output. Defaults to "reset".
        """
        source = DebugLogger._get_caller()
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_code = DebugLogger.COLORS.get(color, DebugLogger.COLORS["reset"])
        print(f"{color_code}[{timestamp}] [{source}][{tag}] {message}{DebugLogger.COLORS['reset']}")

    # ===========================================================
    # Public Helper Methods
    # ===========================================================
    @staticmethod
    def action(msg: str):
        """Log notable player or system actions."""
        DebugLogger._log("ACTION", msg, "action")

    @staticmethod
    def state(msg: str):
        """Log changes in state, mode, or configuration."""
        DebugLogger._log("STATE", msg, "state")

    @staticmethod
    def system(msg: str):
        """Log initialization, setup, or teardown events."""
        DebugLogger._log("SYSTEM", msg, "system")

    @staticmethod
    def warn(msg: str):
        """Log non-fatal warnings and recoverable issues."""
        DebugLogger._log("WARN", msg, "warn")

    @staticmethod
    def trace(msg: str):
        """Low-level debug trace for per-frame or high-frequency events."""
        DebugLogger._log("TRACE", msg, "trace")

    @staticmethod
    def init(msg: str = "", color: str = "init", show_meta: bool = True):
        """
        Log visually-structured initialization text.
        Optionally include timestamp and source metadata.

        Args:
            msg (str): Text to print.
            color (str): Color key (default: 'init' = bright white).
            show_meta (bool): If True, includes timestamp and [Source][INIT] prefix.
        """
        color_code = DebugLogger.COLORS.get(color, DebugLogger.COLORS["init"])
        reset = DebugLogger.COLORS["reset"]

        if not msg.strip():
            print()
            return

        if show_meta:
            source = DebugLogger._get_caller_for_init()
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"{color_code}[{timestamp}] [{source}][INIT] {msg}{reset}")
        else:
            print(f"{color_code}{msg}{reset}")
