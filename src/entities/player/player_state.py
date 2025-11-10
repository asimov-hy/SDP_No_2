"""
player_state.py
---------------
Defines shared enumerations and constants used by all player-related subsystems.

Responsibilities
----------------
- Provide centralized state definitions to prevent circular imports.
- Define interaction states (e.g., invincible, intangible).
- Store universal player-related constants for consistent reference.
"""

from enum import Enum


# ===========================================================
# Player Interaction States
# ===========================================================
class InteractionState(Enum):
    """
    Defines the player's interaction and collision behavior levels.

    Numeric Values
    ---------------
    0 → DEFAULT
        Normal gameplay behavior — takes damage and collides with all entities.
    1 → INVINCIBLE
        Player is immune to damage but still collides physically.
    2 → INTANGIBLE
        Player passes through enemies without damage or contact.
    3 → CLIP_THROUGH
        Debug state — no collision or damage with any entity.
    """
    DEFAULT = 0
    INVINCIBLE = 1
    INTANGIBLE = 2
    CLIP_THROUGH = 3


# ===========================================================
# Shared Player Constants
# ===========================================================
PLAYER_TAG = "player"              # Collision tag identifier for player entity
INVINCIBILITY_DURATION = 1.0       # Duration (in seconds) of post-hit invincibility window
