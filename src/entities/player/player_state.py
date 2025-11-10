"""
player_state.py
---------------
Defines player-specific states, effects, and constants.

Extends the shared InteractionState system from entity_state.py with
player-exclusive temporary effects like invulnerability frames.

Responsibilities
----------------
- Define player-specific effect states (i-frames, dash, etc.)
- Map effects to interaction states, animations, and durations
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
    """Defines player-exclusive temporary effects."""
    NONE = 0
    DAMAGE_IFRAME = auto()
    DASH = auto()
    POWERUP = auto()


# ===========================================================
# Effect → Behavior Mapping
# ===========================================================
EFFECT_RULES = {
    PlayerEffectState.DAMAGE_IFRAME: {
        "interaction": InteractionState.INTANGIBLE,  # Passes through enemies/bullets
        "duration": 1.5,                             # seconds
        "animation": "damage_flash",                 # Animation key to trigger
    },
}


# ===========================================================
# Helper Functions
# ===========================================================
def get_effect_duration(effect: PlayerEffectState) -> float:
    """Get the duration of a player effect in seconds."""
    return EFFECT_RULES.get(effect, {}).get("duration", 0.0)


def get_effect_interaction_state(effect: PlayerEffectState) -> InteractionState:
    """Get the interaction state associated with a player effect."""
    return EFFECT_RULES.get(effect, {}).get("interaction", InteractionState.DEFAULT)


def get_effect_animation(effect: PlayerEffectState) -> str | None:
    """Get the animation key associated with a player effect."""
    return EFFECT_RULES.get(effect, {}).get("animation")


def should_cancel_on_action(effect: PlayerEffectState) -> bool:
    """Check if this effect should cancel when player performs an action."""
    return EFFECT_RULES.get(effect, {}).get("cancel_on_action", False)
