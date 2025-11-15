from src.core.debug.debug_logger import DebugLogger

class ExpManager:
    """
    Manages all EXP-related logic for the player.

    Responsibilities
    ----------------
    - Receive EXP rewards when enemies are defeated
    - Track current EXP and required EXP for next level
    - Determine when a level-up occurs
    - Apply EXP growth curve
    - (Future) Trigger level-up UI and pause gameplay

    Notes
    -----
    This version only handles EXP and level calculations.
    UI handling and pause behavior will be added later.
    """

    def __init__(self, game_state):
        self.game_state = game_state


    # Exp Up
    def exp_up(self, amount: int):
        """
        Called when an enemy is defeated.
        Adds EXP and checks for level-up.
        """
        self.game_state.exp += amount

        DebugLogger.state(
        f"[ExpManager][Exp Up] +{amount} ({self.game_state.exp}/{self.game_state.level_exp})"
        )

        if self.is_level_up():
            self.level_up()


    def is_level_up(self):
        """Return True if current EXP >= required EXP."""
        return self.game_state.exp >= self.game_state.level_exp

    def level_up(self):
        """
        1. Reset EXP
        2. Increase level
        3. Calculate next level EXP
        4. (To be implemented later) Pause game & show LevelUp UI
        """
        self.game_state.exp = 0
        self.game_state.level += 1
        self.game_state.level_exp = self.calculate_next_exp(self.game_state.level)

        DebugLogger.state(
            f"[ExpManager][LEVEL UP] Level : {self.game_state.level} "
            f"(Next Required EXP: {self.game_state.level_exp})"
        )

    def calculate_next_exp(self, lv: int) -> int:
        """Smooth exponential EXP curve."""
        return int(30 * (1.15 ** (lv - 1)))

