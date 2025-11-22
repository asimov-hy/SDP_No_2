"""
session_stats.py
----------------
Tracks statistics for the current game session/run.
Separated from entity management and scene state.
"""


class SessionStats:
    """
    Container for run-specific statistics.
    Reset when starting a new game.
    """

    def __init__(self):
        """Initialize stats to defaults."""
        self.reset()

    def reset(self):
        """Reset all stats to starting values."""
        self.score = 0
        self.high_score = 0
        self.total_score = 0
        self.enemies_killed = 0
        self.items_collected = 0
        self.run_time = 0.0

        # Additional stats can be added dynamically
        self._custom_stats = {}

    # ===========================================================
    # Core Stats Accessors
    # ===========================================================

    def add_score(self, amount: int):
        """Add to current score."""
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

    # ===========================================================
    # Custom Stats (Extensible)
    # ===========================================================

    def get_stat(self, key: str, default=None):
        """
        Get a custom stat value.

        Args:
            key: Stat identifier
            default: Value if stat doesn't exist

        Returns:
            Stat value or default
        """
        return self._custom_stats.get(key, default)

    def set_stat(self, key: str, value):
        """
        Set a custom stat value.

        Args:
            key: Stat identifier
            value: Value to set
        """
        self._custom_stats[key] = value

    def add_stat(self, key: str, amount):
        """
        Increment a custom numerical stat.

        Args:
            key: Stat identifier
            amount: Amount to add
        """
        current = self._custom_stats.get(key, 0)
        self._custom_stats[key] = current + amount

    def has_stat(self, key: str) -> bool:
        """Check if custom stat exists."""
        return key in self._custom_stats

    def remove_stat(self, key: str):
        """Remove a custom stat."""
        if key in self._custom_stats:
            del self._custom_stats[key]


# Global singleton instance
_SESSION_STATS = None

def update_session_stats() -> SessionStats:
    """Get or create the session stats singleton."""
    global _SESSION_STATS
    if _SESSION_STATS is None:
        _SESSION_STATS = SessionStats()
    return _SESSION_STATS
