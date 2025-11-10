"""
player_logic.py
---------------
Player-specific behavior hooks and effect management.

These functions are called by entity_logic.py or directly by player systems.
They handle player-exclusive logic like i-frames, death cleanup, and visuals.
"""

from src.core.utils.debug_logger import DebugLogger
from src.entities import entity_logic
from src.entities.entity_state import InteractionState
from .player_state import (
    PlayerEffectState,
    EFFECT_RULES,
    get_effect_duration,
    get_effect_interaction_state,
    get_effect_animation
)


# ===========================================================
# Entity Hook: Damage Response
# ===========================================================
def on_damaged(player, amount: int):
    """
    Called automatically by entity_logic.apply_damage() after player takes damage.
    Triggers invulnerability frames and visual feedback.
    """
    apply_effect(player, PlayerEffectState.DAMAGE_IFRAME)
    DebugLogger.state(f"[PlayerDamaged] HP={player.health}", category="damage")


# ===========================================================
# Entity Hook: Death Cleanup
# ===========================================================
def on_death(player):
    """
    Called automatically by entity_logic.handle_death() when player HP reaches zero.
    Clears the global player reference for game-over detection.
    """
    from src.core.game_state import STATE
    STATE.player_ref = None
    DebugLogger.state("[PlayerDeath] Player cleanup complete", category="state")


# ===========================================================
# Effect Management
# ===========================================================
def apply_effect(player, effect: PlayerEffectState):
    """
    Apply a temporary effect to the player.

    Sets the interaction state, triggers animation, and starts effect timer.
    """
    if effect == PlayerEffectState.NONE:
        return

    rules = EFFECT_RULES.get(effect)
    if not rules:
        DebugLogger.warn(f"[EffectError] No rules defined for {effect}")
        return

    # Store active effect and timer
    player.active_effect = effect
    player.effect_timer = rules["duration"]

    # Update interaction state (for collision behavior)
    entity_logic.set_interaction_state(player, rules["interaction"])

    # Trigger animation
    animation_key = rules.get("animation")
    if animation_key and hasattr(player, "animation_manager"):
        player.animation_manager.play(animation_key)

    DebugLogger.state(
        f"[EffectApplied] {effect.name} → {rules['interaction'].name} "
        f"(duration={rules['duration']}s)",
        category="state"
    )


def update_effects(player, dt: float):
    """
    Update active player effects each frame.

    Decrements effect timer and clears effect when expired.
    Should be called in Player.update().
    """
    effect = getattr(player, "active_effect", PlayerEffectState.NONE)
    if effect == PlayerEffectState.NONE:
        return

    # Decrement timer
    player.effect_timer = getattr(player, "effect_timer", 0) - dt

    # Check if effect expired
    if player.effect_timer <= 0:
        clear_effect(player)


def clear_effect(player):
    """
    Remove the active effect and return player to normal state.
    """
    effect = getattr(player, "active_effect", PlayerEffectState.NONE)
    if effect == PlayerEffectState.NONE:
        return

    # Reset to default state
    player.active_effect = PlayerEffectState.NONE
    player.effect_timer = 0
    entity_logic.set_interaction_state(player, InteractionState.DEFAULT)

    # Optional: trigger end animation
    # if hasattr(player, "animation_manager"):
    #     player.animation_manager.play("idle")

    DebugLogger.state(f"[EffectCleared] {effect.name} expired", category="state")


# ===========================================================
# Visual Update Hook
# ===========================================================
def update_visual_state(player):
    """
    Player-specific visual feedback based on health and state.

    Called by entity_logic after damage/death events.
    """
    if player.render_mode == "shape":
        # Critical health: red tint
        if player.health <= 1:
            player.color = (255, 80, 80)
        # Normal health: white
        else:
            player.color = (255, 255, 255)

        DebugLogger.state(
            f"[PlayerVisual] HP={player.health} color={player.color}",
            category="effects"
        )

    # Image mode: could swap sprites here
    # elif player.render_mode == "image":
    #     if player.health <= 1:
    #         player.image = player.image_states["damaged"]
    #     else:
    #         player.image = player.image_states["normal"]