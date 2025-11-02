"""
debug_logger.py
---------------
Lightweight console logger for consistent engine debugging output.
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

    @staticmethod
    def _log(source, tag, message, color="reset"):
        t = datetime.now().strftime("%H:%M:%S")
        c = DebugLogger.COLORS.get(color, DebugLogger.COLORS["reset"])
        print(f"{c}[{t}] [{source}][{tag}] {message}{DebugLogger.COLORS['reset']}")

    # Public helpers
    @staticmethod
    def action(source, msg): DebugLogger._log(source, "ACTION", msg, "action")
    @staticmethod
    def state(source, msg):  DebugLogger._log(source, "STATE", msg, "state")
    @staticmethod
    def system(source, msg): DebugLogger._log(source, "SYSTEM", msg, "system")
    @staticmethod
    def warn(source, msg):   DebugLogger._log(source, "WARN", msg, "warn")
