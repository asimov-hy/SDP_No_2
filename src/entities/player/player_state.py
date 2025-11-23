"""
player_state.py
---------------
Defines player-exclusive effects states and constants.

Responsibilities
----------------
- Define player-specific temporary effects (i-frames, dash, etc.)
- Player-exclusive constants only
"""

from enum import IntEnum, auto


class PlayerEffectState(IntEnum):
    """Defines player-exclusive temporary effects."""
    NONE = 0
    IFRAME = auto()