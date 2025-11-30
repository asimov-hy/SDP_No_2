"""
player_ability.py
----------------
Handles player combat-related systems:
- Primary shooting and cooldown management.
- Secondary spread shot with charge mechanic.
"""

import math

from src.core.debug.debug_logger import DebugLogger
from src.entities.bullets.bullet_straight import StraightBullet
from src.entities.player.player_state import PlayerEffectState


# ===========================================================
# Shooting System
# ===========================================================
def update_shooting(player, dt: float):
    """Handle the player's shooting behavior and cooldown timing."""
    # Accumulate time toward next allowed shot
    if player.state_manager.has_state(PlayerEffectState.STUN):
        return

    player.shoot_timer = min(player.shoot_timer + dt, player.shoot_cooldown)

    if player.input.held("attack") and player.shoot_timer >= player.shoot_cooldown:
        player.shoot_timer = max(0, player.shoot_timer - player.shoot_cooldown)
        _fire_bullet(player)


def _fire_bullet(player):
    """
    Spawn a StraightBullet via the BulletManager.
    Uses spawn_custom() for future flexibility (spread, homing, etc.).
    """
    if not player.bullet_manager:
        DebugLogger.warn("Attempted to fire without BulletManager", category="combat")
        return

    # Fire a straight bullet upward (direction can be changed for 8-way later)
    direction = (0, -1)  # Upward for now
    vel = (direction[0] * player.bullet_speed, direction[1] * player.bullet_speed)

    player.bullet_manager.spawn_custom(
        StraightBullet,
        pos=player.rect.center,
        vel=vel,
        owner="player",
    )

    if hasattr(player, "sound_manager") and player.sound_manager:
        player.sound_manager.play_bfx("player_shoot")

    DebugLogger.state("StraightBullet fired", category="combat")


# ===========================================================
# Spread Shot System
# ===========================================================
def update_spread_shot(player, dt: float):
    """Handle charged spread shot with bomb key."""
    if player.state_manager.has_state(PlayerEffectState.STUN):
        player.spread_charging = False
        player.spread_charge = 0.0
        return

    # Cooldown tick
    player.spread_timer = min(player.spread_timer + dt, player.spread_cooldown)

    # Not ready yet
    if player.spread_timer < player.spread_cooldown:
        return

    # Start charging
    if player.input.pressed("bomb"):
        player.spread_charging = True
        player.spread_charge = 0.0

    # Continue charging
    if player.spread_charging and player.input.held("bomb"):
        max_time = player.spread_charge_levels[-1]["time"]
        player.spread_charge = min(player.spread_charge + dt, max_time)

    # Release = fire
    if player.spread_charging and player.input.released("bomb"):
        _fire_spread(player)
        player.spread_charging = False
        player.spread_charge = 0.0
        player.spread_timer = 0.0


def _get_charge_level(player) -> dict:
    """Get current charge level config based on charge time."""
    result = player.spread_charge_levels[0]
    for level in player.spread_charge_levels:
        if player.spread_charge >= level["time"]:
            result = level
    return result


def _fire_spread(player):
    """Fire spread shot based on charge level."""
    if not player.bullet_manager:
        return

    level = _get_charge_level(player)
    count = level["count"]
    half_angle = level["angle"]

    # Calculate angles for each bullet
    if count == 1:
        angles = [0]
    else:
        angles = [
            -half_angle + (2 * half_angle * i / (count - 1))
            for i in range(count)
        ]

    # Spawn bullets
    for angle_deg in angles:
        angle_rad = math.radians(angle_deg - 90)  # -90 = up
        vx = math.cos(angle_rad) * player.spread_speed
        vy = math.sin(angle_rad) * player.spread_speed

        player.bullet_manager.spawn_custom(
            StraightBullet,
            pos=player.rect.center,
            vel=(vx, vy),
            owner="player",
            damage=player.spread_damage,
        )

    if hasattr(player, "sound_manager") and player.sound_manager:
        player.sound_manager.play_bfx("player_shoot")

    DebugLogger.state(
        f"Spread shot: {count} bullets, ±{half_angle}°",
        category="combat"
    )