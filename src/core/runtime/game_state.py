"""
game_state.py
-------------
Holds all mutable runtime state of the game.
Separate from static configuration in game_settings.py.
"""


class GameState:
    def __init__(self):
        # Scene control
        self.current_scene = "start"
        self.previous_scene = None

        # Player & gameplay
        self.score = 0
        self.lives = 3
        self.level = 1
        self.player_ref = None

        # Flags
        self.is_paused = False
        self.is_game_over = False
        self.is_victory = False

        # Session statistics (isolated data container)
        self.stats = {
            "score": 0,
            "high_score": 0,
            "total_score": 0,
            "enemies_killed": 0,
            "items_collected": 0,
            "run_time": 0.0,
        }

    # ===========================================================
    # Stats Accessors
    # ===========================================================
    def get_stat(self, key, default=None):
        """Retrieve a stat value safely."""
        return self.stats.get(key, default)

    def set_stat(self, key, value):
        """Set or overwrite a stat value."""
        self.stats[key] = value

    def add_stat(self, key, amount):
        """Increment a numerical stat. Initializes if missing."""
        self.stats[key] = self.stats.get(key, 0) + amount

    def has_stat(self, key):
        """Check if a stat exists."""
        return key in self.stats

    def remove_stat(self, key):
        """Delete a stat if present."""
        if key in self.stats:
            del self.stats[key]

    def reset(self):
        """Reset state to defaults when starting a new game."""
        self.__init__()


# Global singleton instance for shared access
STATE = GameState()