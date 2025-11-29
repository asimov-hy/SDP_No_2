"""
player_logic.py
---------------
Player-specific behavior hooks and effects management.

These functions are called by entity_logic.py or directly by player systems.
They handle player-exclusive logic like i-frames, death cleanup, and visuals.
"""

from src.core.debug.debug_logger import DebugLogger
from src.core.services.event_manager import PlayerHealthEvent, FireRateEvent, get_events, ScreenShakeEvent
from src.entities.entity_state import LifecycleState
from src.entities.entity_state import InteractionState
from src.entities.player.player_state import PlayerEffectState
from src.graphics.particles.particle_manager import ParticleEmitter


# ===========================================================
# Entity Hook: Damage Response
# ===========================================================
def damage_collision(player, other):
    """
    Handle collision responses with enemies or projectiles.

    Flow:
        - Skip if player is invincible, intangible, or already dead
        - Apply damage and accumulate stress
        - Light damage: flash only, remain vulnerable
        - Heavy damage (stress threshold): STUN state + debuffs
    """
    if player.death_state != LifecycleState.ALIVE:
        DebugLogger.trace("Player already dead", category="collision")
        return

    if player.state_manager.has_state(PlayerEffectState.STUN):
        DebugLogger.trace("Player in STUN - damage blocked", category="collision")
        return

    damage = getattr(other, "damage", 1)
    if damage <= 0:
        DebugLogger.trace(f"Invalid damage value {damage}", category="collision")
        return

    # Check RECOVERY state - shield blocks damage entirely
    in_recovery_state = player.state_manager.has_state(PlayerEffectState.RECOVERY)

    if in_recovery_state:
        recovery_cfg = player.state_manager.get_state_config(PlayerEffectState.RECOVERY)
        knockback = recovery_cfg.get("shield_knockback", 300)

        # Calculate knockback direction
        dx = player.pos.x - other.pos.x
        dy = player.pos.y - other.pos.y
        length = (dx * dx + dy * dy) ** 0.5
        if length > 0:
            player.velocity.x = (dx / length) * knockback
            player.velocity.y = (dy / length) * knockback

        # Shield impact visual
        ParticleEmitter.burst("shield_impact", player.rect.center, count=8,
                              direction=(dx, dy) if length > 0 else None)

        DebugLogger.trace(f"SHIELD BLOCK - knockback applied", category="collision")
        return  # Block all damage

    # Apply damage
    prev_health = player.health
    player.health -= damage
    DebugLogger.action(
        f"Player took {damage} damage ({prev_health} → {player.health})",
        category="collision"
    )

    # Accumulate stress (skip if in RECOVERY)
    if not in_recovery_state:
        player.stress = min(player.stress_max, player.stress + damage * player.stress_per_damage)
        player._time_since_damage = 0.0
    DebugLogger.trace(f"Stress: {player.stress:.1f}/{player.stress_threshold}", category="collision")

    # Calculate knockback direction
    dx = other.pos.x - player.pos.x
    dy = other.pos.y - player.pos.y
    length = (dx * dx + dy * dy) ** 0.5
    direction = (dx / length, dy / length) if length > 0 else None

    # Apply collision knockback (enemy body contact only)
    if getattr(other, "collision_tag", None) == "enemy":
        if player.stress < player.stress_threshold:  # Won't trigger STUN
            collision_kb = player.cfg.get("combat", {}).get("collision_knockback", 200)
            player.apply_knockback(direction, collision_kb)
            player.state_manager.timed_state(PlayerEffectState.KNOCKBACK)

    # Spawn particles
    ParticleEmitter.burst("damage_player", player.pos, count=10, direction=direction)

    # Handle death
    if player.health <= 0:
        on_death(player)
        return

    # Determine visual state
    if player.health <= player._threshold_critical:
        target_state = "damaged_critical"
    elif player.health <= player._threshold_moderate:
        target_state = "damaged_moderate"
    else:
        target_state = "normal"

    previous_state = player._current_sprite

    # Check stress threshold
    if player.stress >= player.stress_threshold:
        _apply_heavy_damage(player, previous_state, target_state, direction)
        player.stress = 0.0
    else:
        _apply_light_damage(player, previous_state, target_state)


def _apply_light_damage(player, previous_state, target_state):
    """Flash + particles only. No invincibility."""
    DebugLogger.state(f"Light damage: {previous_state} → {target_state}", category="animation")

    player.anim_manager.play(
        "damage",
        duration=0.3,
        blink_interval=0.05,
        previous_state=previous_state,
        target_state=target_state
    )
    # No state change - player remains vulnerable


def _apply_heavy_damage(player, previous_state, target_state, direction):
    """STUN → DAMAGED chain."""
    get_events().dispatch(ScreenShakeEvent(intensity=12.0, duration=0.4))
    stun_cfg = player.state_manager.state_config.get("stun", {})
    stun_duration = stun_cfg.get("duration", 0.5)
    knockback = stun_cfg.get("knockback_strength", 400)

    DebugLogger.state(f"HEAVY damage! Entering STUN", category="animation")

    # Apply stun knockback (replaces collision knockback with stronger force)
    player.apply_knockback(direction, knockback)

    # Play STUN animation (short, white flash)
    player.anim_manager.play(
        "stun",
        duration=stun_duration,
        previous_state=previous_state,
        target_state=target_state
    )

    # Enter STUN (auto-chains to DAMAGED via config)
    player.state_manager.timed_state(PlayerEffectState.STUN)


def _apply_recovery_hit(player, previous_state, target_state):
    """Hit while in RECOVERY state - brief flash only."""
    DebugLogger.state(f"Hit during RECOVERY state", category="animation")

    player.anim_manager.play(
        "damage",
        duration=0.2,
        blink_interval=0.05,
        previous_state=previous_state,
        target_state=target_state
    )


def on_death(player):
    """
    Called automatically by entity_logic.handle_death() when player HP reaches zero.
    Clears the global player reference for game-over detection.
    """

    DebugLogger.state("Player death triggered", category="player")

    # Start the death animation
    player.anim_manager.play("death", duration=2.0)

    # Enter DYING state (BaseEntity handles this)
    player.mark_dead()

    # Disable collisions during death animation
    player.collision_tag = "neutral"
