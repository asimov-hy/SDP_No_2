"""
player_logic.py
---------------
Player-specific behavior hooks and effect management.

These functions are called by entity_logic.py or directly by player systems.
They handle player-exclusive logic like i-frames, death cleanup, and visuals.
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState
from src.entities.player.player_state import PlayerEffectState, InteractionState
from src.graphics.animations.entities_animation.player_animation import damage_player, death_player


# ===========================================================
# Entity Hook: Damage Response
# ===========================================================
def damage_collision(player, other):
    """
    Handle collision responses with enemies or projectiles.

    Flow:
        - Skip if player is invincible, intangible, or already dead
        - Skip if any temporary effect (e.g., iframe) is active
        - Retrieve damage value from collided entity
        - Apply damage and trigger IFRAME via EffectManager
    """
    if player.death_state != LifecycleState.ALIVE:
        DebugLogger.trace("Player already dead", category="collision")
        return

    # Skip collisions if player is in non-default state
    if player.state is not InteractionState.DEFAULT:
        DebugLogger.trace(f"PlayerState = {player.state.name}", category="collision")
        return

    # Determine damage value from the other entity
    damage = getattr(other, "damage", 1)
    if damage <= 0:
        DebugLogger.trace(f"Invalid damage value {damage}", category="collision")
        return

    # Apply damage
    prev_health = player.health
    player.health -= damage
    DebugLogger.action(
        f"Player took {damage} damage ({prev_health} → {player.health})",
        category="collision"
    )

    # Handle player death
    if player.health <= 0:
        on_death(player)
        return

    # Determine target visual state
    if player.health <= player._threshold_critical:
        target_state = "damaged_critical"
    elif player.health <= player._threshold_moderate:
        target_state = "damaged_moderate"
    else:
        target_state = "normal"

    iframe_time = player.status_manager.effect_config["iframe"]["duration"]
    previous_state = player._current_sprite  # Get OLD state before damage

    DebugLogger.state(
        f"Visual transition: {previous_state} → {target_state}",
        category="animation"
    )

    player.anim.play(
        damage_player,
        duration=iframe_time,
        blink_interval=0.1,
        previous_state=previous_state,
        target_state=target_state
    )

    # Trigger IFRAME and update visuals
    player.status_manager.activate(PlayerEffectState.IFRAME)


def on_death(player):
    """
    Called automatically by entity_logic.handle_death() when player HP reaches zero.
    Clears the global player reference for game-over detection.
    """

    DebugLogger.state("Player death triggered", category="player")

    # Start the death animation
    player.anim.play(death_player, duration=1.0)

    # Enter DYING state (BaseEntity handles this)
    player.mark_dead()

    # Disable collisions during death animation
    player.collision_tag = "neutral"


# ===========================================================
# Item Effect Application
# ===========================================================
def apply_item_effects(player, effects: list):
    """
    Apply item effects directly to player.
    Called by items on collision.

    Args:
        player: Player entity
        effects: List of effect dicts from items.json
    """
    if player.death_state != LifecycleState.ALIVE:
        return

    for effect in effects:
        effect_type = effect.get("type")

        if effect_type == "ADD_PLAYER_HEALTH":
            amount = effect.get("amount", 0)
            old_health = player.health
            player.health = min(player.max_health, player.health + amount)

            DebugLogger.action(
                f"Health +{amount} ({old_health} → {player.health})",
                category="item"
            )

        elif effect_type == "MULTIPLY_FIRE_RATE":
            multiplier = effect.get("multiplier", 1.0)
            duration = effect.get("duration", 0)

            if not hasattr(player, '_original_shoot_cooldown'):
                player._original_shoot_cooldown = player.shoot_cooldown

            player.shoot_cooldown = player._original_shoot_cooldown / multiplier

            DebugLogger.action(
                f"Fire rate {multiplier}x for {duration}s",
                category="item"
            )
            # TODO: Add duration handling via status_manager

        else:
            DebugLogger.warn(f"Unknown effect type: {effect_type}", category="item")
