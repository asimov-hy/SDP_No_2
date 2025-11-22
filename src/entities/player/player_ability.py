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

    # Get damage bonus and multishot count modifiers
    damage_bonus = player.state_manager.get_stat("damage_bonus", 1.0)
    multishot = int(player.state_manager.get_stat("multishot_count", 0))
    
    # Get player position and fire bullets
    pos = player.rect.center
    
    # Fire the main bullet (center)
    player.bullet_manager.spawn_custom(
        StraightBullet,
        pos=pos,
        vel=(0, -900),
        image=player.bullet_image,
        radius=4,
        owner="player",
        damage_bonus=damage_bonus,
    )
    
    # Fire additional bullets if multishot is available
    if multishot > 0:
        # Create spread pattern for multishot bullets
        for i in range(multishot):
            # Calculate spread angle (alternating left and right)
            angle_degrees = (i + 1) * 15  # 15 degrees per additional shot
            if (i + 1) % 2 == 0:  # Even shots go right
                angle_degrees = -angle_degrees
                
            # Convert to radians and calculate velocity vector
            import math
            angle_rad = math.radians(angle_degrees)
            vel_x = math.sin(angle_rad) * 900
            vel_y = -math.cos(angle_rad) * 900
            
            # Fire the additional bullet
            player.bullet_manager.spawn_custom(
                StraightBullet,
                pos=pos,
                vel=(vel_x, vel_y),
                image=player.bullet_image,
                radius=4,
                owner="player",
                damage_bonus=damage_bonus,
            )

    DebugLogger.state(f"StraightBullet fired (damage: {damage_bonus}x, multishot: {multishot})", category="combat")
