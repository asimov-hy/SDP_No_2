"""
waypoint_shooter.py
----------------
Shooting enemy with configurable movement patterns.

Responsibilities
----------------
- Shoot bullets at configurable intervals
- Support linear movement (like EnemyStraight)
- Support waypoint-based movement (moves between positions)
- Calculate aim direction toward player or fixed direction
"""

import math
import pygame
from src.systems.entity_management.entity_registry import EntityRegistry
from src.entities.enemies.base_enemy import BaseEnemy
from src.entities import EntityCategory
from src.core.debug.debug_logger import DebugLogger


class WaypointShooter(BaseEnemy):
    """Enemy that shoots bullets while moving."""

    __slots__ = ('waypoint_speed', 'waypoints', 'current_waypoint_index',
                 'shoot_interval', 'shoot_timer', 'bullet_speed', 'bullet_image',
                 'player_ref', 'bullet_manager')

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "waypoint_shooter"
    _cached_defaults = None

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, speed=None, health=None, size=None, draw_manager=None,
                 waypoints=None, waypoint_speed=None, shoot_interval=None, bullet_speed=None,
                 player_ref=None, bullet_manager=None, **kwargs):
        """
        JSON-driven shooter enemy with optional overrides.
        """
        if WaypointShooter._cached_defaults is None:
            WaypointShooter._cached_defaults = EntityRegistry.get_data("enemy", "waypoint_shooter")
        defaults = WaypointShooter._cached_defaults

        speed = speed if speed is not None else defaults.get("speed", 100)
        health = health if health is not None else defaults.get("hp", 2)

        scale = defaults.get("scale", 1.0)

        waypoint_speed = waypoint_speed if waypoint_speed is not None else defaults.get("waypoint_speed", 120)
        waypoints = waypoints if waypoints is not None else defaults.get("waypoints", None)

        shoot_interval = shoot_interval if shoot_interval is not None else defaults.get("shoot_interval", 1.25)
        bullet_speed = bullet_speed if bullet_speed is not None else defaults.get("bullet_speed", 300)

        # Load and scale bullet image
        bullet_image_path = defaults.get("bullet_image", "assets/images/null.png")
        bullet_scale = defaults.get("bullet_scale", 0.3)
        bullet_img = pygame.image.load(bullet_image_path).convert_alpha()
        original_size = bullet_img.get_size()
        new_size = (int(original_size[0] * bullet_scale), int(original_size[1] * bullet_scale))
        self.bullet_image = pygame.transform.scale(bullet_img, new_size)

        image_path = defaults.get("image", "assets/images/null.png")
        hitbox_config = defaults.get("hitbox", {})

        # norm_size = (size, size) if isinstance(size, int) else size

        # ============================
        # Load sprite
        # ============================
        # Calculate scale from target size
        img = pygame.image.load(image_path).convert_alpha()
        w, h = img.get_size()
        img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))

        super().__init__(
            x, y,
            image=img,
            draw_manager=draw_manager,
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge", None),
            hitbox_config=hitbox_config
        )

        # Store EXP from JSON
        self.exp_value = defaults.get("exp", 0)

        # Always waypoint movement
        self.waypoints = waypoints or [(x, y)]
        self.waypoint_speed = waypoint_speed
        self.current_waypoint_index = 0
        self.velocity = pygame.Vector2(0, 0)
        self._update_waypoint_velocity()

        self.shoot_interval = shoot_interval
        self.shoot_timer = 0.0
        self.bullet_speed = bullet_speed
        self.player_ref = player_ref
        self.bullet_manager = bullet_manager
        self._rotation_enabled = True

        DebugLogger.init(
            f"Spawned WaypointShooter at ({x}, {y}) | Waypoints={len(self.waypoints)} | ShootInterval={shoot_interval}",
            category="enemy"
        )

    # ===========================================================
    # Update Logic
    # ===========================================================
    def _update_behavior(self, dt: float):
        self.shoot_timer += dt
        if self.shoot_timer >= self.shoot_interval:
            self._shoot()
            self.shoot_timer = 0.0
        self._update_waypoint_movement(dt)
        self._rotate_towards_player()

    def _update_waypoint_movement(self, dt: float):
        """Move toward current waypoint, cycle to next when reached."""
        if not self.waypoints or len(self.waypoints) == 0:
            return

        target = self.waypoints[self.current_waypoint_index]

        # Optimization: Use raw x,y instead of Vector2 subtraction
        dx = target[0] - self.pos.x
        dy = target[1] - self.pos.y

        # distance squared
        dist_sq = dx*dx + dy*dy

        # Reached waypoint threshold (5px -> 25px squared)
        if dist_sq < 25:
            self.current_waypoint_index = (self.current_waypoint_index + 1) % len(self.waypoints)
            self._update_waypoint_velocity()
        elif dist_sq > 0:
            # Manually normalize and apply speed
            dist = math.sqrt(dist_sq)
            self.velocity.x = (dx / dist) * self.waypoint_speed
            self.velocity.y = (dy / dist) * self.waypoint_speed

    def _update_waypoint_velocity(self):
        """Calculate velocity toward next waypoint."""
        if not self.waypoints:
            return

        target = self.waypoints[self.current_waypoint_index]

        # Direct assignment
        dx = target[0] - self.pos.x
        dy = target[1] - self.pos.y

        dist_sq = dx*dx + dy*dy

        if dist_sq > 0:
            dist = math.sqrt(dist_sq)
            self.velocity.x = (dx / dist) * self.waypoint_speed
            self.velocity.y = (dy / dist) * self.waypoint_speed

    def _rotate_towards_player(self):
        """Rotate sprite to face player."""
        if not self._rotation_enabled or not self._base_image or self.player_ref is None:
            return

        # Calculate direction to player
        dx = self.player_ref.pos.x - self.pos.x
        dy = self.player_ref.pos.y - self.pos.y

        # Skip if too close (avoid jitter)
        dist_sq = dx * dx + dy * dy
        if dist_sq < 1.0:
            return

        # Calculate angle (assuming sprite faces UP by default)
        direction = pygame.Vector2(dx, dy)
        angle = -pygame.Vector2(0, -1).angle_to(direction)

        # Normalize to 0-360
        angle = angle % 360

        # Calculate cache index
        index = int(round(angle / self.ROTATION_INCREMENT)) % self.ROTATION_STEPS

        # Apply rotation if changed
        if index != self._cached_rotation_index:
            self.image = self._get_rotated_surface(index)
            self.rect = self.image.get_rect(center=self.rect.center)
            self._cached_rotation_index = index
            self.rotation_angle = index * self.ROTATION_INCREMENT

    # ===========================================================
    # Shooting
    # ===========================================================
    def _shoot(self):
        """Spawn a bullet toward player."""
        if self.bullet_manager is None or self.player_ref is None:
            return

        # Calculate direction to player
        dx = self.player_ref.pos.x - self.pos.x
        dy = self.player_ref.pos.y - self.pos.y
        dist_sq = dx * dx + dy * dy

        if dist_sq > 0:
            inv_dist = 1.0 / math.sqrt(dist_sq)
            dir_x = dx * inv_dist
            dir_y = dy * inv_dist
        else:
            dir_x, dir_y = 0.0, 1.0

        # Spawn bullet with image
        self.bullet_manager.spawn(
            pos=(self.pos.x, self.pos.y),
            vel=(dir_x * self.bullet_speed, dir_y * self.bullet_speed),
            image=self.bullet_image,
            owner="enemy",
            damage=1
        )

    # ===========================================================
    # Reset for Object Pooling
    # ===========================================================
    def reset(self, x, y, speed=150, health=3, size=60,
              waypoints=None, waypoint_speed=100, shoot_interval=1.0,
              bullet_speed=300, player_ref=None, **kwargs):
        """Reset waypoint shooter for pooling."""

        # Reset base properties
        super().reset(
            x, y,
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge")
        )

        # Update size if changed
        if size != getattr(self, 'size', None):
            self.size = size
            norm_size = (size, size) if isinstance(size, int) else size
            # Reload and scale image
            if hasattr(self, '_base_image') and self._base_image:
                self.image = pygame.transform.scale(self._base_image, norm_size)
                self.rect = self.image.get_rect(center=self.pos)

        # Always waypoint movement
        self.waypoints = waypoints or [(x, y)]
        self.waypoint_speed = waypoint_speed
        self.current_waypoint_index = 0
        self._update_waypoint_velocity()

        # Reset shooting parameters
        self.shoot_interval = shoot_interval
        self.shoot_timer = 0.0
        self.bullet_speed = bullet_speed
        self.player_ref = player_ref

        # self.sync_rect() -> Removed: Redundant (handled by super().reset and refresh_sprite)
