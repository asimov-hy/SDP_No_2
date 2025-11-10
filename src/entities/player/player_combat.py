"""
player_combat.py
----------------
Handles all player combat-related systems:
- Shooting and cooldown management.
- Collision damage and invulnerability logic.
"""

import pygame
from src.core.utils.debug_logger import DebugLogger
from .player_state import InteractionState


# ===========================================================
# Shooting System
# ===========================================================
def update_shooting(player, dt: float):
    """
    Manage shooting cooldowns and fire bullets when input is triggered.

    Args:
        player (Player): The player entity.
        dt (float): Delta time since the last frame (seconds).
    """
    player.shoot_timer += dt
    keys = pygame.key.get_pressed()

    # Fire bullet when spacebar pressed and cooldown elapsed
    if keys[pygame.K_SPACE] and player.shoot_timer >= player.shoot_cooldown:
        player.shoot_timer = 0.0
        shoot(player)


def shoot(player):
    """
    Fire a bullet upward from the player's position via BulletManager.

    Args:
        player (Player): The player entity.
    """
    if not player.bullet_manager:
        DebugLogger.warn("Attempted to shoot without BulletManager")
        return

    player.bullet_manager.spawn(
        pos=player.rect.center,
        vel=(0, -900),  # Upward trajectory
        color=(255, 255, 100),
        radius=4,
        owner="player",
    )
    DebugLogger.state("Player fired bullet", category="user_action")


# ===========================================================
# Collision & Damage
# ===========================================================
def damage_collision(player, other):
    """
    Handle collision responses with enemies or projectiles.

    Behavior:
        - Check player state (invincible/intangible, etc.)
        - Retrieve damage value from the collided entity
        - Apply damage if valid

    Args:
        player (Player): The player entity.
        other (BaseEntity): The entity collided with.
    """

    # 1) Validate state before taking damage
    if player.state is not InteractionState.DEFAULT:
        DebugLogger.state(f"Ignored damage due to state: {player.state.name}", category="combat")
        return

    # 2) Retrieve damage value
    damage = getattr(other, "damage", 1)
    if not isinstance(damage, (int, float)) or damage <= 0:
        DebugLogger.warn(f"Invalid or missing damage value from {getattr(other, 'collision_tag', 'unknown')}")
        return

    # 3) Apply damage
    player.take_damage(damage)

    # 4) Handle player death
    if not player.alive:
        DebugLogger.state("Player death triggered by collision", category="combat")
