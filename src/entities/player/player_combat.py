"""
player_combat.py
----------------
Handles player combat-related systems:
- Shooting and cooldown management.
- Collision damage routing through entity_logic.
"""

from src.core.utils.debug_logger import DebugLogger
from src.entities.bullets.bullet_straight import StraightBullet
from src.entities.player.player_state import InteractionState
from src.entities.entity_state import LifecycleState


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
        DebugLogger.warn("[PlayerCombat] Attempted to fire without BulletManager", category="combat")
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

    DebugLogger.state("[PlayerFire] StraightBullet fired", category="combat")


# ===========================================================
# Collision & Damage
# ===========================================================
def damage_collision(player, other):
    """
    Handle collision responses with enemies or projectiles.

    Flow:
        - Check interaction state (invincible, intangible, etc.)
        - Retrieve damage value from collided entity
        - Route through entity_logic.apply_damage()

    Args:
        player (Player): The player entity.
        other (BaseEntity): The entity collided with.
    """

    if player.state is not InteractionState.DEFAULT:
        return

    if player.death_state != LifecycleState.ALIVE:
        return

    damage = getattr(other, "damage", 1)
    if damage <= 0:
        return

    player.health -= damage
    from .player_logic import update_visual_state
    update_visual_state(player)

    # Trigger animations/visuals
    from .player_logic import on_damage
    on_damage(player, damage)  # Handles hit animation

    if player.health <= 0:
        from .player_logic import on_death
        player.mark_dead()
        on_death(player)
