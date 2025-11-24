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
    """Enemy that tracks the player with configurable homing modes."""

    __slots__ = ('turn_rate', 'player_ref', 'update_delay', 'update_timer', 'spawn_edge')

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "homing"
    _cached_defaults = None

    # Homing mode configurations
    HOMING_CONFIG = {
        "default": {"turn_rate": 90, "update_delay": 0, "speed_boost": 0},     # Slow constant turning
        "efficient": {"turn_rate": 180, "update_delay": 0, "speed_boost": 0},  # Fast constant turning
        "smarter": {"turn_rate": 9999, "update_delay": 1.0, "speed_boost": 0}, # Instant snap every 1.0s
        # "launcher": {"turn_rate": 9999, "update_delay": 999.0, "speed_boost": 500}  # One-time aim + speed boost
    }

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=None, health=None,
                 scale=None, draw_manager=None,
                 homing_mode="default", player_ref=None, **kwargs):
        """
        Args:
            x, y: Spawn position
            direction: Tuple (dx, dy) for movement direction
            speed: Pixels per second (override, or use JSON default)
            health: HP before death (override, or use JSON default)
            scale: Size override (or use JSON default)
            draw_manager: Required for sprite loading
            homing_mode: "default", "efficient", "smarter", or "launcher"
            player_ref: Reference to player for homing calculations
        """
        # Load defaults from JSON
        if EnemyHoming._cached_defaults is None:
            EnemyHoming._cached_defaults = EntityRegistry.get_data("enemy", "homing")
        defaults = EnemyHoming._cached_defaults

        # Apply overrides or use defaults
        speed = speed if speed is not None else defaults.get("speed", 150)
        health = health if health is not None else defaults.get("hp", 1)
        scale = scale if scale is not None else defaults.get("scale", 1.0)

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

        # Homing configuration - always enabled
        config = self.HOMING_CONFIG.get(homing_mode, self.HOMING_CONFIG["default"])
        self.turn_rate = config["turn_rate"]
        self.update_delay = config["update_delay"]
        self.player_ref = player_ref
        self.update_timer = 0.0  # For delayed update modes
        self.spawn_edge = kwargs.get("spawn_edge")

        # self.speed_boost_applied = False  # Track if launcher speed boost was applied
        # # Apply speed boost for launcher mode
        # if config.get("speed_boost", 0) > 0:
        #     self.speed += config["speed_boost"]

        # Store exp value
        self.exp_value = defaults.get("exp", 0)

        self._rotation_enabled = False

        DebugLogger.init(
            f"Spawned EnemyHoming at ({x}, {y}) | Speed={speed} | Mode={homing_mode}",
            category="animation_effects"
        )

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Move the enemy and handle homing if player exists.

        Args:
            dt (float): Delta time (in seconds) since last frame.
        """
        if self.player_ref:
            if self.update_delay > 0:
                # Delayed update modes (smarter, launcher)
                self.update_timer += dt
                if self.update_timer >= self.update_delay:
                    self._update_homing_continuous(dt)
                    self.update_timer = 0.0
            else:
                # Constant update modes (default, efficient)
                self._update_homing_continuous(dt)

        super().update(dt)

    def reset(self, x, y, direction=(0, 1), speed=200, health=1, size=50, color=(255, 0, 0), **kwargs):
        """Reset enemy for pooling."""
        super().reset(
            x, y,
            direction=direction,
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge")
        )

        norm_size = (size, size) if isinstance(size, int) else size

        # Update shape_data for new size/color
        self.shape_data = {
            "type": "circle",
            "size": norm_size,
            "color": color
        }

        # Rebuild image if draw_manager available
        if self.draw_manager:
            self.refresh_sprite(new_color=color, size=norm_size)

        # Update homing mode if provided
        if "homing_mode" in kwargs:
            config = self.HOMING_CONFIG.get(kwargs["homing_mode"], self.HOMING_CONFIG["default"])
            self.turn_rate = config["turn_rate"]
            self.update_delay = config["update_delay"]
            self.update_timer = 0.0

            # self.speed_boost_applied = False
            # # Apply speed boost for launcher mode
            # if config.get("speed_boost", 0) > 0:
            #     self.speed += config["speed_boost"]

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