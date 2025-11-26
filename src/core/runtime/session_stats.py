"""
session_stats.py
----------------
Tracks statistics for the current game session/run.
Separated from entity management and scene state.
"""


# ===========================================================
# Session Stats
# ===========================================================

class SessionStats:
    """Container for run-specific statistics. Reset when starting a new game."""

    def __init__(self):
        self.score = 0
        self.high_score = 0
        self.total_score = 0
        self.enemies_killed = 0
        self.items_collected = 0
        self.run_time = 0.0
        self.max_level_reached = 1
        self.total_exp_gained = 0
        self._custom_stats = {}

    # ===========================================================
    # Core Stats
    # ===========================================================

    def add_score(self, amount: int):
        """Add to current score and update high score."""
        self.score += amount
        self.total_score += amount
        if self.score > self.high_score:
            self.high_score = self.score

    def add_kill(self):
        """Increment enemy kill count."""
        self.enemies_killed += 1

    def add_item(self):
        """Increment item collection count."""
        self.items_collected += 1

    def add_time(self, dt: float):
        """Add elapsed time to run timer."""
        self.run_time += dt

    def add_exp(self, amount: int):
        """Add experience gained."""
        self.total_exp_gained += amount

    def set_level(self, level: int):
        """Update max level if higher."""
        if level > self.max_level_reached:
            self.max_level_reached = level

    # ===========================================================
    # Custom Stats
    # ===========================================================

    def get_stat(self, key: str, default=None):
        """Get a custom stat value."""
        return self._custom_stats.get(key, default)

    def set_stat(self, key: str, value):
        """Set a custom stat value."""
        self._custom_stats[key] = value

    def add_stat(self, key: str, amount):
        """Increment a custom numerical stat."""
        current = self._custom_stats.get(key, 0)
        self._custom_stats[key] = current + amount

    def has_stat(self, key: str) -> bool:
        """Check if custom stat exists."""
        return key in self._custom_stats

    def remove_stat(self, key: str):
        """Remove a custom stat."""
        self._custom_stats.pop(key, None)

    # ===========================================================
    # Lifecycle
    # ===========================================================

    def reset(self):
        """Reset all stats for new run. Preserves high score."""
        self.score = 0
        self.total_score = 0
        self.enemies_killed = 0
        self.items_collected = 0
        self.run_time = 0.0
        self.max_level_reached = 1
        self.total_exp_gained = 0
        self._custom_stats.clear()

    def full_reset(self):
        """Reset everything including high score."""
        self.reset()
        self.high_score = 0


# ===========================================================
# Singleton Access
# ===========================================================

_SESSION_STATS = None


def get_session_stats() -> SessionStats:
    """Get or create the session stats singleton."""
    global _SESSION_STATS
    if _SESSION_STATS is None:
        _SESSION_STATS = SessionStats()
    return _SESSION_STATS


def reset_session_stats() -> None:
    """Reset the singleton. Call on full game restart."""
    global _SESSION_STATS
    _SESSION_STATS = None