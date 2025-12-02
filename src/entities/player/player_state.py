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
    KNOCKBACK = auto()  # Brief input lock, not invincible
    STUN = auto()  # Knockback, no input, invincible
    RECOVERY = auto()  # Debuffed, invincible
