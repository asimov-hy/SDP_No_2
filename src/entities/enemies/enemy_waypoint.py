"""
enemy_waypoint.py
-----------------
Defines a waypoint-following enemy that patrols between fixed positions.

Responsibilities
----------------
- Move between a list of waypoints in sequence
- Loop continuously through waypoints until destroyed
- Use velocity-based movement with automatic rotation
"""

import pygame
from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.base_entity import BaseEntity
from src.entities import EntityCategory
from src.core.debug.debug_logger import DebugLogger
from src.systems.entity_management.entity_registry import EntityRegistry


class EnemyWaypoint(BaseEnemy):
    """Enemy that follows a fixed path through waypoints."""

    __slots__ = ('waypoints', 'current_waypoint_idx', 'arrival_threshold')

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "waypoint"
    _cached_defaults = None

    def __init__(self, x, y, waypoints=None, speed=None, health=None,
                 scale=None, draw_manager=None, **kwargs):
        """
        Args:
            x, y: Spawn position
            waypoints: List of (x, y) tuples defining the patrol path
            speed: Movement speed (override or use JSON default)
            health: HP (override or use JSON default)
            scale: Image scale (override or use JSON default)
            draw_manager: Required for sprite loading
        """
        # Load defaults from JSON
        if EnemyWaypoint._cached_defaults is None:
            EnemyWaypoint._cached_defaults = EntityRegistry.get_data("enemy", "waypoint")
        defaults = EnemyWaypoint._cached_defaults

        # Apply overrides or use defaults
        speed = speed if speed is not None else defaults.get("speed", 200)
        health = health if health is not None else defaults.get("hp", 2)
        scale = scale if scale is not None else defaults.get("scale", 0.1)

        image_path = defaults.get("image", "assets/images/sprites/enemies/missile.png")
        hitbox_config = defaults.get("hitbox", {})

        # Load and scale image
        img = BaseEntity.load_and_scale_image(image_path, scale)

        super().__init__(
            x, y,
            image=img,
            draw_manager=draw_manager,
            speed=speed,
            health=health,
            direction=(0, 1),  # Initial direction (overwritten by waypoint system)
            spawn_edge=kwargs.get("spawn_edge"),
            hitbox_config=hitbox_config
        )

        # Waypoint system
        self.waypoints = waypoints or []
        self.current_waypoint_idx = 0
        self.arrival_threshold = 10  # pixels

        # Store exp value
        self.exp_value = defaults.get("exp", 60)

        # Start moving to first waypoint
        if self.waypoints and len(self.waypoints) > 0:
            self._update_velocity_to_next_waypoint()

        DebugLogger.init(
            f"Spawned EnemyWaypoint at ({x}, {y}) | Waypoints={len(self.waypoints)}",
            category="animation_effects"
        )

    def update(self, dt: float):
        """
        Move toward current waypoint and advance when reached.
        Loops through waypoints continuously.
        """
        if self.waypoints and len(self.waypoints) > 1:
            target = pygame.Vector2(self.waypoints[self.current_waypoint_idx])
            distance = self.pos.distance_to(target)

            # Check if arrived at waypoint
            if distance < self.arrival_threshold:
                # Advance to next waypoint (loop back to start)
                self.current_waypoint_idx = (self.current_waypoint_idx + 1) % len(self.waypoints)
                self._update_velocity_to_next_waypoint()

        # BaseEnemy.update() handles movement and rotation
        super().update(dt)

    def _update_velocity_to_next_waypoint(self):
        """Calculate velocity toward next waypoint."""
        if not self.waypoints:
            return

        target = pygame.Vector2(self.waypoints[self.current_waypoint_idx])
        direction = target - self.pos

        if direction.length() > 0:
            direction.normalize_ip()
            self.velocity = direction * self.speed

    def reset(self, x, y, waypoints=None, speed=None, health=None, scale=None, **kwargs):
        """Reset enemy for pooling."""
        # Load defaults from JSON
        defaults = EnemyWaypoint._cached_defaults

        speed = speed if speed is not None else defaults.get("speed", 200)
        health = health if health is not None else defaults.get("hp", 2)
        scale = scale if scale is not None else defaults.get("scale", 0.1)
        image_path = defaults.get("image")
        hitbox_scale = defaults.get("hitbox", {}).get("scale", 0.85)

        # Update exp value
        self.exp_value = defaults.get("exp", 60)

        # Reset waypoint system
        self.waypoints = waypoints or []
        self.current_waypoint_idx = 0

        # Call super to reset position/state
        super().reset(
            x, y,
            direction=(0, 1),
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge"),
            hitbox_scale=hitbox_scale
        )

        # Reload image if using image mode
        if image_path:
            self._reload_image_cached(image_path, scale)

        # Start moving to first waypoint
        if self.waypoints and len(self.waypoints) > 0:
            self._update_velocity_to_next_waypoint()