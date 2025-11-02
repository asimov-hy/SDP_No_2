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

from datetime import datetime

class DebugLogger:
    """Global logger with consistent, colorized, source-tagged output."""

    COLORS = {
        "reset": "\033[0m",
        "action": "\033[92m",   # Green
        "state":  "\033[96m",   # Cyan
        "warn":   "\033[93m",   # Yellow
        "system": "\033[95m",   # Magenta
    }

    # ===========================================================
    # Core Logging Utility
    # ===========================================================
    @staticmethod
    def _log(source: str, tag: str, message: str, color: str = "reset"):
        """
        Core log formatter.

        Args:
            source (str): The name of the module or class emitting the log.
            tag (str): The type of log message (e.g., SYSTEM, STATE, ACTION, WARN).
            message (str): Descriptive message to display.
            color (str, optional): Color key for terminal output. Defaults to "reset".
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_code = DebugLogger.COLORS.get(color, DebugLogger.COLORS["reset"])
        print(f"{color_code}[{timestamp}] [{source}][{tag}] {message}{DebugLogger.COLORS['reset']}")

    # ===========================================================
    # Public Helper Methods
    # ===========================================================
    @staticmethod
    def action(source: str, msg: str):
        """Log notable player or system actions."""
        DebugLogger._log(source, "ACTION", msg, "action")

    @staticmethod
    def state(source: str, msg: str):
        """Log changes in state, mode, or configuration."""
        DebugLogger._log(source, "STATE", msg, "state")

    @staticmethod
    def system(source: str, msg: str):
        """Log initialization, setup, or teardown events."""
        DebugLogger._log(source, "SYSTEM", msg, "system")

    @staticmethod
    def warn(source: str, msg: str):
        """Log non-fatal warnings and recoverable issues."""
        DebugLogger._log(source, "WARN", msg, "warn")
