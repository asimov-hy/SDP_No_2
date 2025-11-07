"""
game_state.py
-------------
Holds all mutable runtime state of the game.
Separate from static configuration in settings.py.
"""

class GameState:
    def __init__(self):
        # Scene control
        self.current_scene = "start"  # start, game, pause, etc.
        self.previous_scene = None

        # Player & gameplay
        self.score = 0
        self.lives = 3
        self.level = 1
        self.player_ref = None  # Can hold player instance reference

        # Flags
        self.is_paused = False
        self.is_game_over = False
        self.is_victory = False

    def reset(self):
        """Reset state to defaults when starting a new game."""
        self.__init__()


# Global singleton instance for shared access
STATE = GameState()
