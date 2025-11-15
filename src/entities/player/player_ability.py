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
def update_shooting(player, dt: float, attack_held: bool):
    """
    Handle the player's shooting behavior and cooldown timing.

    Args:
        player (Player): The player instance controlling the shot.
        dt (float): Delta time since the last frame (in seconds).
        attack_held (bool): Whether the attack input is currently held.
    """
    # Accumulate time toward next allowed shot
    player.shoot_timer = min(player.shoot_timer + dt, player.shoot_cooldown)

    if attack_held and player.shoot_timer >= player.shoot_cooldown:
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

    # Fire a straight bullet upward
    player.bullet_manager.spawn_custom(
        StraightBullet,
        pos=player.rect.center,
        vel=(0, -900),  # Upward trajectory
        color=(255, 255, 100),
        radius=4,
        owner="player",
    )

    DebugLogger.state("StraightBullet fired", category="combat")