"""
dummy_item.py
-------------
Defines the DummyItem class, a basic item that modifies player lives.

Responsibilities
----------------
- Provide a concrete implementation of the Item abstract class.
- Modify the player's lives through the GameState upon effect application.
"""

from src.core.utils.debug_logger import DebugLogger
from src.entities.items.item import Item
from src.core.game_state import GameState


class DummyItem(Item):
    """A simple item that changes the player's lives."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image, game_state: GameState):
        """
        Initializes the DummyItem.

        Args:
            game_state (GameState): Reference to the current game state.
        """
        super().__init__(x, y, image)
        self.game_state = game_state
        self.lives_change = 1  # Amount to change player lives
        DebugLogger.init("║{:<59}║".format(f"	[DummyItem][INIT]	→  Initialized"), show_meta=False)

    # ===========================================================
    # Effect Application
    # ===========================================================
    def apply_effect(self):
        """
        Applies the item's effect, increasing player lives in GameState.
        """
        self.game_state.lives += self.lives_change
        DebugLogger.action("║{:<59}║".format(f"	[DummyItem][ACTION]	→  Player lives changed by: {self.lives_change}"))