"""
enemy_homing.py
-----------------
Defines a homing enemy capable of tracking the player.

Responsibilities
----------------
- Implement continuous homing with configurable modes.
- Support slow gradual turning or instant snapping behaviors.
"""

import pygame
import math
from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory
from src.core.debug.debug_logger import DebugLogger
from src.systems.entity_management.entity_registry import EntityRegistry


class EnemyHoming(BaseEnemy):
    """Enemy that tracks the player with configurable turn rates and speeds."""

    __slots__ = ('turn_rate', 'player_ref', 'update_delay', 'update_timer', 'spawn_edge', 'enemy_type')

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "homing"
    _cached_defaults = {}

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=None, health=None,
                 scale=None, draw_manager=None, player_ref=None, **kwargs):
        """
        Args:
            x, y: Spawn position
            direction: Tuple (dx, dy) for movement direction
            speed: Pixels per second (override, or use JSON default)
            health: HP before death (override, or use JSON default)
            scale: Size override (or use JSON default)
            draw_manager: Required for sprite loading
            player_ref: Reference to player for homing calculations
        """
        # Derive enemy type from registry name
        enemy_type = self.__registry_name__

        # Cache defaults per enemy type
        if enemy_type not in EnemyHoming._cached_defaults:
            EnemyHoming._cached_defaults[enemy_type] = EntityRegistry.get_data("enemy", enemy_type)
        defaults = EnemyHoming._cached_defaults[enemy_type]

        # Apply overrides or use defaults from JSON
        speed = speed if speed is not None else defaults.get("speed", 300)
        health = health if health is not None else defaults.get("hp", 3)
        scale = scale if scale is not None else defaults.get("scale", 0.5)

        # Read homing behavior from JSON
        turn_rate = defaults.get("turn_rate", 180)
        update_delay = defaults.get("update_delay", 0)

        image_path = defaults.get("image")
        hitbox_config = defaults.get("hitbox", {})

        # Load and scale image using helper
        img = BaseEntity.load_and_scale_image(image_path, scale)

        super().__init__(
            x, y,
            image=img,
            draw_manager=draw_manager,
            speed=speed,
            health=health,
            direction=direction,
            spawn_edge=kwargs.get("spawn_edge"),
            hitbox_config=hitbox_config
        )

        # Homing configuration from JSON
        self.enemy_type = enemy_type
        self.turn_rate = turn_rate
        self.update_delay = update_delay
        self.player_ref = player_ref
        self.update_timer = 0.0  # For delayed update modes
        self.spawn_edge = kwargs.get("spawn_edge")

        # Store exp value
        self.exp_value = defaults.get("exp", 75)

        self._rotation_enabled = False

        DebugLogger.init(
            f"Spawned {enemy_type} at ({x}, {y}) | Speed={speed} | Turn={turn_rate}",
            category="animation_effects"
        )

    # ===========================================================
    # Update Logic
    # ===========================================================
    def _update_behavior(self, dt: float):
        if self.player_ref:
            if self.update_delay > 0:
                self.update_timer += dt
                if self.update_timer >= self.update_delay:
                    self._update_homing_continuous(dt)
                    self.update_timer = 0.0
            else:
                self._update_homing_continuous(dt)

    def reset(self, x, y, direction=(0, 1), speed=None, health=None, **kwargs):
        """Reset enemy for pooling."""
        # Derive enemy type from registry name
        enemy_type = self.__registry_name__
        # Reload defaults for new enemy type
        if enemy_type not in EnemyHoming._cached_defaults:
            EnemyHoming._cached_defaults[enemy_type] = EntityRegistry.get_data("enemy", enemy_type)
        defaults = EnemyHoming._cached_defaults[enemy_type]

        speed = speed if speed is not None else defaults.get("speed", 300)
        health = health if health is not None else defaults.get("hp", 3)

        super().reset(
            x, y,
            direction=direction,
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge")
        )

        # Update homing parameters from JSON
        self.enemy_type = enemy_type
        self.turn_rate = defaults.get("turn_rate", 180)
        self.update_delay = defaults.get("update_delay", 0)
        self.update_timer = 0.0

        if "player_ref" in kwargs:
            self.player_ref = kwargs["player_ref"]

        if "spawn_edge" in kwargs:
            self.spawn_edge = kwargs["spawn_edge"]

    def _update_homing_continuous(self, dt):
        """Smooth turn toward player each frame (or instant snap for high turn_rate)"""
        if not self.player_ref or not hasattr(self.player_ref, 'pos'):
            return

        # Calculate direction to player
        to_player = self.player_ref.pos - self.pos
        if to_player.length() == 0:
            return

        target_dir = to_player.normalize()
        current_dir = self.velocity.normalize() if self.velocity.length() > 0 else pygame.Vector2(0, 1)

        # Calculate angle difference
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

class EnemyHomingSlow(EnemyHoming):
    __registry_name__ = "homing_slow"

class EnemyHomingFast(EnemyHoming):
    __registry_name__ = "homing_fast"

class EnemyHomingSmart(EnemyHoming):
    __registry_name__ = "homing_smart"