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
        print("ded")
        on_death(player)
        return
    print("not ded")

    # Determine target visual state
    if player.health <= player._threshold_critical:
        target_state = "damaged_critical"
    elif player.health <= player._threshold_moderate:
        target_state = "damaged_moderate"
    else:
        target_state = "normal"

    iframe_time = player.status_manager.effect_config["iframe"]["duration"]
    previous_state = player._current_visual_state  # Get OLD state before damage

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


# ===========================================================
# Entity Hook: Death Cleanup
# ===========================================================
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
# Visual Update Hook
# ===========================================================
# def update_visual_state(player):
#     """Update player visuals based on health thresholds from config."""
#     health = player.health
#     if health == player._cached_health:
#         return
#
#     player._cached_health = health
#
#     # Determine state
#     if health <= player._threshold_critical:
#         state_key = "damaged_critical"
#     elif health <= player._threshold_moderate:
#         state_key = "damaged_moderate"
#     else:
#         state_key = "normal"
#
#     player._current_visual_state = state_key
#
#     if player.render_mode == "shape":
#         player.refresh_visual(new_color=player.get_target_color(state_key))
#     else:
#         new_image = player.get_target_image(state_key)
#         if new_image:
#             player.refresh_visual(new_image=new_image)
