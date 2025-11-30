"""
player_ability.py
----------------
Handles player combat-related systems:
- Primary shooting and cooldown management.
- Secondary spread shot with charge mechanic.
"""

import math
import random

from src.core.debug.debug_logger import DebugLogger
from src.entities.bullets.bullet_straight import StraightBullet
from src.entities.player.player_state import PlayerEffectState
from src.graphics.particles.particle_manager import ParticleEmitter, Particle, SpriteCache

# Charge color gradient: blue -> cyan -> yellow -> white
CHARGE_COLORS = [
    (100, 180, 255),   # 0% - Blue
    (100, 255, 255),   # 33% - Cyan
    (255, 255, 100),   # 66% - Yellow
    (255, 255, 255),   # 100% - White
]


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
    max_time = player.spread_charge_levels[-1]["time"]

    # Stunned = charge fails
    if player.state_manager.has_state(PlayerEffectState.STUN):
        if player.spread_charging:
            ParticleEmitter.burst("spread_charge_fail", player.rect.center, count=12)
            DebugLogger.state("Spread charge interrupted!", category="combat")
        player.spread_charging = False
        player.spread_charge = 0.0
        player._spread_max_reached = False
        return

    # Cooldown tick
    player.spread_timer = min(player.spread_timer + dt, player.spread_cooldown)

    # Not ready yet
    if player.spread_timer < player.spread_cooldown:
        if player.input.pressed("bomb"):
            ParticleEmitter.burst("spread_charge_fail", player.rect.center, count=6)
            DebugLogger.state("Spread shot on cooldown!", category="combat")
        return

    # Start charging
    if player.input.pressed("bomb"):
        player.spread_charging = True
        player.spread_charge = 0.0
        player._spread_max_reached = False
        player._charge_emit_timer = 0.0

    # Continue charging
    if player.spread_charging and player.input.held("bomb"):
        prev_charge = player.spread_charge
        player.spread_charge = min(player.spread_charge + dt, max_time)

        # Emit inward charging particles
        _emit_charge_particles_inward(player, dt)

        # Check if max charge just reached
        if prev_charge < max_time and player.spread_charge >= max_time:
            if not getattr(player, '_spread_max_reached', False):
                player._spread_max_reached = True
                ParticleEmitter.burst("spread_charge_full", player.rect.center, count=20)
                DebugLogger.state("Spread shot FULLY CHARGED!", category="combat")

    # Release = fire
    if player.spread_charging and player.input.released("bomb"):
        _fire_spread(player)
        player.spread_charging = False
        player.spread_charge = 0.0
        player.spread_timer = 0.0
        player._spread_max_reached = False


def _get_charge_color(charge_ratio: float) -> tuple:
    """Interpolate color based on charge ratio (0.0 to 1.0)."""
    if charge_ratio >= 1.0:
        return CHARGE_COLORS[-1]

    # Find which segment we're in
    segment_count = len(CHARGE_COLORS) - 1
    scaled = charge_ratio * segment_count
    idx = int(scaled)
    t = scaled - idx

    # Lerp between two colors
    c1 = CHARGE_COLORS[idx]
    c2 = CHARGE_COLORS[min(idx + 1, len(CHARGE_COLORS) - 1)]

    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


def _emit_charge_particles_inward(player, dt: float):
    """Emit particles - inward while charging, outward when fully charged."""
    if not hasattr(player, '_charge_emit_timer'):
        player._charge_emit_timer = 0.0

    player._charge_emit_timer += dt
    max_time = player.spread_charge_levels[-1]["time"]
    charge_ratio = player.spread_charge / max_time
    is_fully_charged = charge_ratio >= 1.0

    # Emit rate: faster when fully charged (pulsing effect)
    if is_fully_charged:
        emit_interval = 0.04
    else:
        emit_interval = 0.08 - (0.05 * charge_ratio)

    if player._charge_emit_timer >= emit_interval:
        player._charge_emit_timer = 0.0

        color = _get_charge_color(charge_ratio)
        cx, cy = player.rect.center

        if is_fully_charged:
            # OUTWARD burst - radiating "ready" effect
            count = 4
            for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                speed = random.uniform(120, 200)

                # Spawn at center, move outward
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                size = random.randint(4, 8)
                lifetime = random.uniform(0.3, 0.5)

                particle = Particle(
                    x=cx, y=cy,
                    vx=vx, vy=vy,
                    size=size,
                    color=color,
                    lifetime=lifetime,
                    glow=True,
                    shrink=True
                )
                ParticleEmitter._active_particles.append(particle)
        else:
            # INWARD gathering - charging effect
            count = 2 + int(charge_ratio * 3)
            for _ in range(count):
                angle = random.uniform(0, 2 * math.pi)
                spawn_dist = random.uniform(40, 70)

                spawn_x = cx + math.cos(angle) * spawn_dist
                spawn_y = cy + math.sin(angle) * spawn_dist

                speed = random.uniform(150, 250)
                vx = -math.cos(angle) * speed
                vy = -math.sin(angle) * speed

                size = random.randint(3, 6 + int(charge_ratio * 3))
                lifetime = spawn_dist / speed

                particle = Particle(
                    x=spawn_x, y=spawn_y,
                    vx=vx, vy=vy,
                    size=size,
                    color=color,
                    lifetime=lifetime,
                    glow=True,
                    shrink=True
                )
                ParticleEmitter._active_particles.append(particle)


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