"""
enemy_shooter.py
----------------
Shooting enemy with configurable movement patterns.

Responsibilities
----------------
- Shoot bullets at configurable intervals
- Support linear movement (like EnemyStraight)
- Support waypoint-based movement (moves between positions)
- Calculate aim direction toward player or fixed direction
"""

import pygame
from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory
from src.core.debug.debug_logger import DebugLogger


class EnemyShooter(BaseEnemy):
    """Enemy that shoots bullets while moving."""

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "shooter"

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, speed=None, health=None, size=None, draw_manager=None, movement_type=None,
                 waypoints=None, waypoint_speed=None, shoot_interval=None, bullet_speed=None, bullet_color=None,
                 bullet_radius=None, aim_at_player=None, player_ref=None, bullet_manager=None, **kwargs):
        """
        JSON-driven shooter enemy with optional overrides.
        """
        import pygame
        from src.entities.entity_registry import EntityRegistry

        if draw_manager is None:
            raise ValueError("EnemyShooter requires draw_manager")

        # ============================
        # Load defaults from JSON
        # ============================
        defaults = EntityRegistry.get_data("enemy", "shooter")

        speed = speed if speed is not None else defaults.get("speed", 100)
        health = health if health is not None else defaults.get("hp", 2)
        size = size if size is not None else defaults.get("size", 60)

        movement_type = movement_type if movement_type is not None else defaults.get("movement_type", "linear")
        waypoint_speed = waypoint_speed if waypoint_speed is not None else defaults.get("waypoint_speed", 120)
        waypoints = waypoints if waypoints is not None else defaults.get("waypoints", None)

        shoot_interval = shoot_interval if shoot_interval is not None else defaults.get("shoot_interval", 1.25)
        bullet_speed = bullet_speed if bullet_speed is not None else defaults.get("bullet_speed", 300)
        bullet_color = bullet_color if bullet_color is not None else tuple(defaults.get("bullet_color", [255, 200, 0]))
        bullet_radius = bullet_radius if bullet_radius is not None else defaults.get("bullet_radius", 6)

        aim_at_player = aim_at_player if aim_at_player is not None else defaults.get("aim_at_player", True)

        image_path = defaults.get("image", "assets/images/sprites/enemies/shooter.png")
        hitbox_config = defaults.get("hitbox", {})

        norm_size = (size, size) if isinstance(size, int) else size

        # ============================
        # Load sprite
        # ============================
        # Calculate scale from target size
        temp_img = pygame.image.load(image_path).convert_alpha()
        scale = (norm_size[0] / temp_img.get_width(), norm_size[1] / temp_img.get_height())
        img = BaseEntity.load_and_scale_image(image_path, scale)

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

        # ============================
        # Store parameters for movement
        # ============================
        self.movement_type = movement_type
        self.base_speed = speed

        if movement_type == "waypoint":
            self.waypoints = waypoints or [(x, y)]
            self.waypoint_speed = waypoint_speed
            self.current_waypoint_index = 0
            self.velocity = pygame.Vector2(0, 0)
            self._update_waypoint_velocity()

        # ============================
        # Shooting configuration
        # ============================
        self.shoot_interval = shoot_interval
        self.shoot_timer = 0.0
        self.bullet_speed = bullet_speed
        self.bullet_color = bullet_color
        self.bullet_radius = bullet_radius

        self.aim_at_player = aim_at_player
        self.player_ref = player_ref
        self.bullet_manager = bullet_manager

        from src.core.debug.debug_logger import DebugLogger
        DebugLogger.init(
            f"Spawned EnemyShooter at ({x}, {y}) | Move={movement_type} | ShootInterval={shoot_interval}",
            category="enemy"
        )

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """Update movement and shooting."""
        # Update shooting timer
        self.shoot_timer += dt
        if self.shoot_timer >= self.shoot_interval:
            self._shoot()
            self.shoot_timer = 0.0

        # Update movement based on type
        if self.movement_type == "waypoint":
            self._update_waypoint_movement(dt)

        # Call base update for position sync and offscreen check
        super().update(dt)

    def _update_waypoint_movement(self, dt: float):
        """Move toward current waypoint, cycle to next when reached."""
        if not self.waypoints or len(self.waypoints) == 0:
            return

        target = pygame.Vector2(self.waypoints[self.current_waypoint_index])
        direction = target - self.pos
        distance = direction.length()

        # Reached waypoint threshold
        if distance < 5:
            self.current_waypoint_index = (self.current_waypoint_index + 1) % len(self.waypoints)
            self._update_waypoint_velocity()
        elif distance > 0:
            self.velocity = direction.normalize() * self.waypoint_speed

    def _update_waypoint_velocity(self):
        """Calculate velocity toward next waypoint."""
        if not self.waypoints:
            return

        target = pygame.Vector2(self.waypoints[self.current_waypoint_index])
        direction = target - self.pos
        if direction.length() > 0:
            self.velocity = direction.normalize() * self.waypoint_speed

    # ===========================================================
    # Shooting
    # ===========================================================
    def _shoot(self):
        """Spawn a bullet toward player or in fixed direction."""
        if self.bullet_manager is None:
            return

        # Calculate bullet direction
        if self.aim_at_player and self.player_ref:
            target_pos = pygame.Vector2(self.player_ref.pos)
            direction = target_pos - self.pos
            if direction.length() > 0:
                direction = direction.normalize()
            else:
                direction = pygame.Vector2(0, 1)
        else:
            # Shoot in velocity direction, or downward if stationary
            if self.velocity.length() > 0:
                direction = self.velocity.normalize()
            else:
                direction = pygame.Vector2(0, 1)

        bullet_vel = direction * self.bullet_speed

        # Spawn bullet via bullet_manager
        self.bullet_manager.spawn(
            pos=self.pos,
            vel=bullet_vel,
            color=self.bullet_color,
            radius=self.bullet_radius,
            owner="enemy",
            damage=1
        )

    # ===========================================================
    # Reset for Object Pooling
    # ===========================================================
    def reset(self, x, y, direction=(0, 1), speed=150, health=3, size=60,
              color=(255, 128, 0), movement_type="linear", waypoints=None,
              waypoint_speed=100, shoot_interval=1.0, bullet_speed=300,
              bullet_color=(255, 200, 0), bullet_radius=5, aim_at_player=False,
              player_ref=None, **kwargs):
        """Reset shooter enemy parameters for pooling."""
        # Rebake shape if size or color changed
        if size != self.size or color != self.color:
            self.size = size
            self.color = color
            self.image = self.draw_manager.prebake_shape(
                type="rect",
                size=(size, size),
                color=color
            )
            self.rect = self.image.get_rect(center=(x, y))

        # Reset base properties
        super().reset(
            x, y,
            direction=direction,
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge")
        )

        self.base_speed = speed

        self.movement_type = movement_type
        if movement_type == "linear":
            # BaseEnemy.reset already assigned correct velocity
            pass
        elif movement_type == "waypoint":
            self.waypoints = waypoints or [(x, y)]
            self.waypoint_speed = waypoint_speed
            self.current_waypoint_index = 0
            self._update_waypoint_velocity()

        # Reset shooting
        self.shoot_interval = shoot_interval
        self.shoot_timer = 0.0
        self.bullet_speed = bullet_speed
        self.bullet_color = bullet_color
        self.bullet_radius = bullet_radius
        self.aim_at_player = aim_at_player
        self.player_ref = player_ref

        self.sync_rect()