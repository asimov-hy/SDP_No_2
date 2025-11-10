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

from enum import Enum, auto
from src.entities.entity_state import InteractionState, CollisionTags

# ===========================================================
# Player Constants
# ===========================================================
PLAYER_TAG = CollisionTags.PLAYER  # Use the centralized constant


# ===========================================================
# Player Effect States
# ===========================================================
class PlayerEffectState(Enum):
    """
    Temporary effects applied to the player.

    These are time-limited buffs/debuffs that change how the player
    interacts with the game world. Each effect maps to an InteractionState,
    animation, and duration.

    Effects:
        NONE: No active effect (normal gameplay)
        DAMAGE_IFRAME: Post-damage invulnerability frames
        DODGE: Dash/dodge ability (future)
        PHASE: Phase through walls (future)
    """
    NONE = auto()
    DAMAGE_IFRAME = auto()
    # Future expansion:
    # DODGE = auto()
    # PHASE = auto()
    # POWERUP = auto()


# ===========================================================
# Effect → Behavior Mapping
# ===========================================================
EFFECT_RULES = {
    PlayerEffectState.DAMAGE_IFRAME: {
        "interaction": InteractionState.INTANGIBLE,  # Passes through enemies/bullets
        "duration": 1.5,                             # seconds
        "animation": "damage_flash",                 # Animation key to trigger
        "cancel_on_action": False,                   # Don't cancel if player shoots
    },

    # Example future effects:
    # PlayerEffectState.DODGE: {
    #     "interaction": InteractionState.INTANGIBLE,
    #     "duration": 0.3,
    #     "animation": "dash",
    #     "cancel_on_action": False,
    # },
    #
    # PlayerEffectState.PHASE: {
    #     "interaction": InteractionState.CLIP_THROUGH,
    #     "duration": 2.0,
    #     "animation": "ghost",
    #     "cancel_on_action": True,
    # },
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