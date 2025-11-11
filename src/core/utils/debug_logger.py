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

        "init": "\033[97m",   # Bright white
        "system": "\033[95m", # Magenta
        "action": "\033[92m", # Green
        "state": "\033[96m",  # Cyan
        "warn": "\033[93m",   # Yellow
        "trace": "\033[94m",  # Blue
    }

    # ===========================================================
    # Internal Helpers
    # ===========================================================
    @staticmethod
    def _get_caller():
        """Detect the class or module where the logger was invoked (not defined)."""
        stack = inspect.stack()
        for i, frame in enumerate(stack):
            if frame.function in ("_log", "init"):
                depth = i + 2
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

    @staticmethod
    def _build_prefix(timestamp, source, tag, meta_mode):
        time = f"[{timestamp}]"
        source_ = f"[{source}]"
        tag_ = f"[{tag}]"

        modes = {
            "full": f"{time} {source_}{tag_} ",
            "no_time": f"{source_}{tag_} ",
            "no_source": f"{time} {tag_} ",
            "no_tag": f"{time} {source_} ",
            "time": f"{time} ",
            "source": f"{source_} ",
            "tag": f"{tag_} ",
            "none": ""
        }
        return modes.get(meta_mode, modes["full"])

    # ===========================================================
    # Logger Filtering
    # ===========================================================
    @staticmethod
    def _should_log(category: str, level: str) -> bool:
        """Check if this log type and category should print."""
        if not LoggerConfig.ENABLE_LOGGING:
            return False
        if category not in LoggerConfig.CATEGORIES:
            return False
        if not LoggerConfig.CATEGORIES[category]:
            return False
        order = ["NONE", "ERROR", "WARN", "INFO", "VERBOSE"]
        if order.index(level) > order.index(LoggerConfig.LOG_LEVEL):
            return False
        return True

    # ===========================================================
    # Tree Indentation Helper
    # ===========================================================
    @staticmethod
    def _build_tree_indent(sub: int, is_last: bool = False) -> str:
        """Generate a tree-like indentation pattern."""
        if sub <= 0:
            return ""
        lines = []
        # lines.append(" "*13)
        for i in range(1, sub):
            lines.append("│   ")
        lines.append("└─ " if is_last else "├─ ")
        return "".join(lines)

    # ===========================================================
    # Core Logging Utility
    # ===========================================================
    @staticmethod
    def _log(tag: str, message: str, color: str = "reset",
             category: str = "system", level: str = "INFO",
             meta_mode: str = "full", sub: int = 0, is_last: bool = False):
        """
        Core log formatter with filtering, indentation, and metadata display.
        Supports tree-like indentation through 'sub' and 'is_last'.
        """
        if not DebugLogger._should_log(category, level):
            return

        color_code = DebugLogger.COLORS.get(color, DebugLogger.COLORS["reset"])
        reset = DebugLogger.COLORS["reset"]

        timestamp = datetime.now().strftime("%H:%M:%S")
        source = DebugLogger._get_caller()
        prefix = DebugLogger._build_prefix(timestamp, source, tag, meta_mode)
        indent = DebugLogger._build_tree_indent(sub, is_last)

        print(f"{color_code}{indent}{prefix}{message}{reset}")

    # ===========================================================
    # Public Helper Methods
    # ===========================================================
    @staticmethod
    def action(msg: str, category: str = "system", meta_mode: str = "full", sub: int = 0, is_last: bool = False):
        DebugLogger._log("ACTION", msg, "action", category, "INFO", meta_mode, sub, is_last)

    @staticmethod
    def state(msg: str, category: str = "system", meta_mode: str = "full", sub: int = 0, is_last: bool = False):
        DebugLogger._log("STATE", msg, "state", category, "INFO", meta_mode, sub, is_last)

    @staticmethod
    def system(msg: str, category: str = "system", meta_mode: str = "full", sub: int = 0, is_last: bool = False):
        DebugLogger._log("SYSTEM", msg, "system", category, "INFO", meta_mode, sub, is_last)

    @staticmethod
    def warn(msg: str, category: str = "system", meta_mode: str = "full", sub: int = 0, is_last: bool = False):
        DebugLogger._log("WARN", msg, "warn", category, "WARN", meta_mode, sub, is_last)

    @staticmethod
    def trace(msg: str, category: str = "collision", meta_mode: str = "full", sub: int = 0, is_last: bool = False):
        DebugLogger._log("TRACE", msg, "trace", category, "VERBOSE", meta_mode, sub, is_last)

    @staticmethod
    def init(msg: str = "", category: str = "system", meta_mode: str = "full", sub: int = 0, is_last: bool = False):
        """Initialization log — same as normal log, but white and allows blank line spacing."""
        if not msg.strip():
            print()
            return
        DebugLogger._log("INIT", msg, "init", category, "INFO", meta_mode, sub, is_last)
