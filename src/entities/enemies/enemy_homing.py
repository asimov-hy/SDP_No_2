"""
enemy_straight.py
-----------------
Defines a simple downward-moving enemy for early gameplay testing.

Responsibilities
----------------
- Move straight down the screen at a constant speed.
- Destroy itself when off-screen.
- Serve as a baseline template for other enemy types.
"""

import pygame
from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.entity_state import EntityCategory
from src.core.debug.debug_logger import DebugLogger


class EnemyHoming(BaseEnemy):
    """Simple enemy that moves vertically downward and disappears when off-screen."""

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "homing"

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=200, health=1,
                 size=50, color=(0, 128, 255), draw_manager=None,
                 homing=False, turn_rate=180, player_ref=None, **kwargs):
        """
        Args:
            x, y: Spawn position
            direction: Tuple (dx, dy) for movement direction
            speed: Pixels per second
            health: HP before death
            size: Triangle size (equilateral if int, else (w, h))
            color: RGB tuple
            draw_manager: Required for triangle creation
            homing: False, True (continuous), or "snapshot"
            turn_rate: Degrees per second for continuous homing
            player_ref: Reference to player for homing calculations
        """
        # Create triangle sprite
        if draw_manager is None:
            raise ValueError("EnemyStraight requires draw_manager for triangle creation")

        circle_image = draw_manager.create_circle(size, color)

        # Initialize base enemy
        super().__init__(x, y, circle_image, speed, health)

        # Set velocity from direction
        self.velocity = pygame.Vector2(direction).normalize() * self.speed

        # NEW: Homing support
        self.homing = homing
        self.turn_rate = turn_rate if homing else 0
        self.player_ref = player_ref if homing else None

        # Snapshot homing state
        if homing == "snapshot":
            self.lock_delay = kwargs.get("lock_delay", 0.5)
            self.lock_timer = 0.0
            self.locked = False

        DebugLogger.init(
            f"Spawned EnemyHoming  at ({x}, {y}) | Speed={speed} | Homing={homing}",
            category="animation_effects"
        )

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Move the enemy and handle homing if enabled.

        Args:
            dt (float): Delta time (in seconds) since last frame.
        """
        # NEW: Homing logic before base update
        if self.homing == True and self.player_ref:  # Continuous
            self._update_homing_continuous(dt)
        elif self.homing == "snapshot" and self.player_ref:
            self._update_homing_snapshot(dt)

        super().update(dt)

    def reset(self, x, y, direction=(0, 1), speed=200, health=1, size=50, color=(255, 0, 0), **kwargs):
        """Reset homing enemy with new parameters."""
        super().reset(x, y, **kwargs)

        # Regenerate sprite if size/color changed (optional optimization: only if different)
        if self.draw_manager:
            self._base_image = self.draw_manager.create_triangle(size, color, pointing="up")
            self.image = self._base_image.copy()

        # Reset physics
        self.speed = speed
        self.health = health
        self.max_health = health
        self.velocity = pygame.Vector2(direction).normalize() * speed

        # Reset rotation state
        self.rotation_angle = 0

        # Force immediate rotation update to match velocity
        self.update_rotation()

    def _update_homing_continuous(self, dt):
        """Smooth turn toward player each frame"""
        if not self.player_ref or not hasattr(self.player_ref, 'pos'):
            return

        # Calculate direction to player
        to_player = self.player_ref.pos - self.pos
        if to_player.length() == 0:
            return

        target_dir = to_player.normalize()
        current_dir = self.velocity.normalize() if self.velocity.length() > 0 else pygame.Vector2(0, 1)

        # Calculate angle difference
        import math
        target_angle = math.degrees(math.atan2(target_dir.y, target_dir.x))
        current_angle = math.degrees(math.atan2(current_dir.y, current_dir.x))

        angle_diff = target_angle - current_angle
        # Normalize to -180 to 180
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360

        # Clamp rotation by turn_rate
        max_rotation = self.turn_rate * dt
        rotation = max(-max_rotation, min(max_rotation, angle_diff))

        # Apply rotation
        new_angle = current_angle + rotation
        rad = math.radians(new_angle)
        self.velocity = pygame.Vector2(math.cos(rad), math.sin(rad)) * self.speed

    def _update_homing_snapshot(self, dt):
        """Lock onto player after delay, then go straight"""
        if not self.player_ref or not hasattr(self.player_ref, 'pos'):
            return

        if not self.locked:
            self.lock_timer += dt
            if self.lock_timer >= self.lock_delay:
                # Lock direction to player
                to_player = self.player_ref.pos - self.pos
                if to_player.length() > 0:
                    self.velocity = to_player.normalize() * self.speed
                self.locked = True
