"""
player_state.py
---------------
Defines player-specific states, animation_effects, and constants.

Extends the shared InteractionState system from entity_state.py with
player-exclusive temporary animation_effects like invulnerability frames.

Responsibilities
----------------
- Define player-specific effect states (i-frames, dash, etc.)
- Map animation_effects to interaction states, animations, and durations
- Provide player-exclusive constants
"""

from enum import IntEnum, auto


class InteractionState(IntEnum):
    """
    Defines how the entity collider interacts with others.

    Determines how collisions affect the entity and its surroundings.

    Collision Meaning:
      self        → entity receives damage
      opponent    → collision opponent interacts with entity
      hazard      → entity takes damage from environmental hazards
      environment → interacts physically with walls or terrain

    State Levels:
      0 -> DEFAULT       self: O   opponent: O   hazard: O   environment: O
      1 -> INVINCIBLE    self: X   opponent: O   hazard: O   environment: O
      2 -> INTANGIBLE    self: X   opponent: X   hazard: X   environment: O
      3 -> CLIP_THROUGH  self: X   opponent: X   hazard: X   environment: X
    """
    DEFAULT = 0
    INVINCIBLE = 1
    INTANGIBLE = 2
    CLIP_THROUGH = 3


# ===========================================================
# Player Effect States
# ===========================================================
class PlayerEffectState(IntEnum):
    """Defines player-exclusive temporary animation_effects."""
    NONE = 0
    IFRAME = auto()
    # DASH = auto()
    # POWERUP = auto()
