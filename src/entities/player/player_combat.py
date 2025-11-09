"""
player_combat.py
----------------
Handles all player combat-related systems:
- Shooting and cooldown management.
- Collision damage and health reduction.
- Blinking and temporary invulnerability after taking damage.
"""

import pygame
from src.core.utils.debug_logger import DebugLogger


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
def on_collision(player, other):
    """
    Handle collision responses with enemies or projectiles.

    Args:
        player (Player): The player entity.
        other (BaseEntity): The entity collided with.
    """
    tag = getattr(other, "collision_tag", "unknown")

    if tag == "enemy" and not player.invincible:
        take_damage(player, 1, source=type(other).__name__)
    elif tag == "enemy_bullet" and not player.invincible:
        DebugLogger.state("Player hit by Enemy Bullet")
        take_damage(player, 1, source="enemy_bullet")
    else:
        DebugLogger.trace(f"Player ignored collision with {tag}")


def take_damage(player, amount, source="unknown"):
    """
    Apply incoming damage, trigger blinking and invulnerability.

    Args:
        player (Player): The player entity.
        amount (int): Amount of health lost.
        source (str): Source of damage (enemy, bullet, etc.)
    """
    if player.invincible:
        DebugLogger.trace(f"Player invincible vs {source}")
        return

    player.health -= amount
    DebugLogger.state(f"Took {amount} damage from {source} → HP={player.health}")

    player.update_visual_state()

    if player.health <= 0:
        player.alive = False
        DebugLogger.state("Player destroyed!")
    else:
        player.blinking = True
        player.blink_timer = 0.0
        player.invincible = True
        disable_hitbox(player)
        DebugLogger.state("Player blinking → temporary invulnerability", category="effects")


# ===========================================================
# Blinking / Invulnerability
# ===========================================================
def update_blinking(player, dt):
    """
    Update blinking visual effect and invulnerability timer.

    Args:
        player (Player): The player entity.
        dt (float): Delta time since last frame (seconds).
    """
    if not player.blinking:
        return

    player.blink_timer += dt

    # Toggle visibility periodically
    player.visible = (int(player.blink_timer / player.blink_interval) % 2 == 0)

    # End blinking period after duration expires
    if player.blink_timer >= player.blink_duration:
        player.blinking = False
        player.blink_timer = 0.0
        player.visible = True
        player.invincible = False
        enable_hitbox(player)
        DebugLogger.state("Blinking ended → vulnerability restored", category="effects")


# ===========================================================
# Hitbox Management
# ===========================================================
def enable_hitbox(player):
    """
    Re-enable player collision detection after invulnerability ends.

    Args:
        player (Player): The player entity.
    """
    if player.hitbox:
        player.hitbox.active = True
        player.has_hitbox = True
        DebugLogger.state("Player hitbox re-enabled (vulnerability restored)", category="effects")


def disable_hitbox(player):
    """
    Temporarily disable collision detection during invulnerability.

    Args:
        player (Player): The player entity.
    """
    if player.hitbox:
        player.hitbox.active = False
        player.has_hitbox = False
        DebugLogger.state("Player hitbox disabled (invincibility active)", category="effects")
