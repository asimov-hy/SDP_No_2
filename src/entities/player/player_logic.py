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

    player.anim.play(damage_player, duration=0.15)

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

    # Trigger IFRAME and update visuals
    update_visual_state(player)
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
def update_visual_state(player):
    """
    Update player visuals based on health thresholds from config.
    """
    health = player.health
    if health == player._cached_health:
        return

    player._cached_health = health

    # Determine state
    if health <= player._threshold_critical:
        state_key = "damaged_critical"
    elif health <= player._threshold_moderate:
        state_key = "damaged_moderate"
    else:
        state_key = "normal"

    if player.render_mode == "shape":
        player.refresh_visual(new_color=player._color_cache[state_key])
    else:
        player.refresh_visual(new_image=player._image_cache[state_key])
