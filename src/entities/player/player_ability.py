"""
player_ability.py
----------------
Handles player combat-related systems:
- Shooting and cooldown management.
- Collision damage routing through entity_logic.
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.bullets.bullet_straight import StraightBullet


# ===========================================================
# Shooting System
# ===========================================================
def update_shooting(player, dt: float):
    """Handle the player's shooting behavior and cooldown timing."""
    # Accumulate time toward next allowed shot
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