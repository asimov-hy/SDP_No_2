"""
player_logic.py
---------------
Player-specific behavior hooks and effect management.

These functions are called by entity_logic.py or directly by player systems.
They handle player-exclusive logic like i-frames, death cleanup, and visuals.
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.player.player_state import PlayerEffectState
from src.graphics.animations.entities_animation.player_animation import death_player

# ===========================================================
# Entity Hook: Damage Response
# ===========================================================
def on_damage(player, amount: int):
    """
    Called automatically by entity_logic.apply_damage() after player takes damage.
    Triggers invulnerability frames and visual feedback.
    """
    DebugLogger.action(f"Player took {amount} damage → activating IFRAME")
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
    player.mark_dead(immediate=False)

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
