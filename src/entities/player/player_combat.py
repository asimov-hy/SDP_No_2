"""
player_combat.py
----------------
Handles all player combat-related systems:
- Shooting and cooldown management.
- Collision damage and invulnerability logic.
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
    damage_value = getattr(other, "damage", 1)  # Default damage is 1 if undefined

    # Skip if player cannot take damage
    if player.effects["invincible"]:
        DebugLogger.trace(f"Collision ignored — player invincible vs {tag}")
        return

    # Skip if player is non-collidable (e.g. phasing, clip state)
    if not player.effects["collidable"]:
        DebugLogger.trace(f"Collision ignored — player non-collidable vs {tag}")
        return

    # Handle damage based on source type
    if tag == "enemy":
        DebugLogger.state(f"Player collided with {type(other).__name__} → damage {damage_value}", category="combat")
        take_damage(player, damage_value, source=type(other).__name__)

    elif tag == "enemy_bullet":
        DebugLogger.state(f"Player hit by enemy bullet → damage {damage_value}", category="combat")
        take_damage(player, damage_value, source="enemy_bullet")

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
    if player.effects["invincible"]:
        DebugLogger.trace(f"Player invincible vs {source}")
        return

    player.health -= amount
    DebugLogger.state(f"Took {amount} damage from {source} → HP={player.health}")

    player.update_visual_state()

    if player.health <= 0:
        player.alive = False
        DebugLogger.state("Player destroyed!")
    else:
        # -------------------------------------------------------
        # Activate invulnerability & disable combat collision
        # -------------------------------------------------------
        player.set_effect("invincible", True)
        player.set_effect("collidable", False)

        if player.hitbox:
            player.hitbox.active = False

        DebugLogger.state("Took Damage -> Temp Invulnerability", category="effects")

        # -------------------------------------------------------
        # Trigger damage animation and restore state after completion
        # -------------------------------------------------------
        if hasattr(player, "animation_manager") and player.animation_manager:
            try:
                player.animation_manager.on_complete = lambda e, a: player.clear_effects()
                player.animation_manager.play("damage", duration=player.invuln_duration)
            except Exception as e:
                DebugLogger.warn(f"Failed to play damage animation: {e}", category="animation")


# ===========================================================
# Effect Management
# ===========================================================
def set_effect(self, name: str, state: bool = True):
    """
    Enable or disable a named player effect safely.

    Args:
        name (str): Effect key from self.effects (e.g. "invincible", "collidable").
        state (bool): True to enable, False to disable.
    """
    if name not in self.effects:
        DebugLogger.warn(f"Attempted to set unknown effect '{name}'", category="effects")
        return

    self.effects[name] = state

    # Sync hitbox and visibility for key states
    if name == "collidable" and self.hitbox:
        self.hitbox.active = state
    if name == "clip_through" and state:
        self.set_effect("collidable", False)  # automatically disable collidable

    DebugLogger.state(f"Effect '{name}' set to {state}", category="effects")


def clear_effects(self, name: str | None = None):
    """
    Clear a specific effect or all effects back to default state.

    Args:
        name (str | None): If provided, only clears that effect. If None, resets all.
    """
    if name:
        # Clear single effect
        if name in self.effects and isinstance(self.effects[name], bool):
            default_state = (name != "invincible" and name != "clip_through")
            self.effects[name] = default_state
            DebugLogger.state(f"Effect '{name}' cleared → {default_state}", category="effects")
        else:
            DebugLogger.warn(f"Tried to clear unknown or non-boolean effect '{name}'", category="effects")
    else:
        # Reset all boolean effects to default
        defaults = {
            "invincible": False,
            "collidable": True,
            "clip_through": False,
        }
        for key, value in defaults.items():
            if key in self.effects:
                self.effects[key] = value

        # Clear all temporary or named active effects
        self.effects["active"].clear()

        if self.hitbox:
            self.hitbox.active = True

        DebugLogger.state("All effects reset to default state", category="effects")
