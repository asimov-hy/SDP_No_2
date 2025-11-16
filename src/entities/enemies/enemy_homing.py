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
from src.entities.entity_types import EntityCategory
from src.core.debug.debug_logger import DebugLogger


class EnemyHoming(BaseEnemy):
    """Simple enemy that moves vertically downward and disappears when off-screen."""

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "homing"

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=None, health=None,
                 size=None, draw_manager=None,
                 homing=False, turn_rate=None, player_ref=None, **kwargs):
        """
        Args:
            x, y: Spawn position
            direction: Tuple (dx, dy) for movement direction
            speed: Pixels per second (override, or use JSON default)
            health: HP before death (override, or use JSON default)
            size: Size override (or use JSON default)
            draw_manager: Required for sprite loading
            homing: False, True (continuous), or "snapshot"
            turn_rate: Degrees per second for continuous homing (override, or use JSON default)
            player_ref: Reference to player for homing calculations
        """
        from src.entities.entity_registry import EntityRegistry

        # Load defaults from JSON
        defaults = EntityRegistry.get_data("enemy", "homing")

        # Apply overrides or use defaults
        speed = speed if speed is not None else defaults.get("speed", 150)
        health = health if health is not None else defaults.get("hp", 1)
        size = size if size is not None else defaults.get("size", 52)
        turn_rate = turn_rate if turn_rate is not None else defaults.get("turn_rate", 180)
        image_path = defaults.get("image")
        hitbox_scale = defaults.get("hitbox", {}).get("scale", 0.9)

        if draw_manager is None:
            raise ValueError("EnemyHoming requires draw_manager")

        norm_size = (size, size) if isinstance(size, int) else size

        # Try loading image, fallback to shape
        if image_path:
            img = pygame.image.load(image_path).convert_alpha()
            img = pygame.transform.scale(img, norm_size)

            super().__init__(
                x, y,
                image=img,
                draw_manager=draw_manager,
                speed=speed,
                health=health,
                direction=direction,
                spawn_edge=kwargs.get("spawn_edge"),
                hitbox_scale=hitbox_scale
            )
        else:
            # Fallback to shape
            shape_data = {
                "type": "circle",
                "size": norm_size,
                "color": defaults.get("color", [0, 128, 255])
            }

            super().__init__(
                x, y,
                shape_data=shape_data,
                draw_manager=draw_manager,
                speed=speed,
                health=health,
                direction=direction,
                spawn_edge=kwargs.get("spawn_edge"),
                hitbox_scale=hitbox_scale
            )

        # Homing support
        self.homing = homing
        self.turn_rate = turn_rate if homing else 0
        self.player_ref = player_ref if homing else None

        # Store exp value
        self.exp_value = defaults.get("exp", 0)

        # Homing support
        self.homing = homing
        self.turn_rate = turn_rate if homing else 0
        self.player_ref = player_ref if homing else None

        # Snapshot homing state
        if homing in ("snapshot", "snapshot_axis"):
            self.lock_delay = kwargs.get("lock_delay", 0.5)
            self.lock_timer = 0.0
            self.locked = False

            # Store spawn edge for axis-locking mode
            if homing == "snapshot_axis":
                self.spawn_edge = kwargs.get("spawn_edge")

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
        if self.homing == True and self.player_ref:  # Continuous
            self._update_homing_continuous(dt)
        elif self.homing == "snapshot" and self.player_ref:
            self._update_homing_snapshot(dt)
        elif self.homing == "snapshot_axis" and self.player_ref:
            self._update_homing_snapshot_axis(dt)

        super().update(dt)

    def reset(self, x, y, direction=(0, 1), speed=200, health=1, size=50, color=(255, 0, 0), **kwargs):
        # Forward auto-direction correctly
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
            self._base_image = self.image

        # Update homing mode if pool respawn passes new params
        if "homing" in kwargs:
            self.homing = kwargs["homing"]

        if "turn_rate" in kwargs:
            self.turn_rate = kwargs["turn_rate"] if self.homing else 0

        if "player_ref" in kwargs:
            self.player_ref = kwargs["player_ref"] if self.homing else None

        # Snapshot reset
        if self.homing in ("snapshot", "snapshot_axis"):
            self.lock_delay = kwargs.get("lock_delay", getattr(self, "lock_delay", 0.5))
            self.lock_timer = 0.0
            self.locked = False

            # Update spawn_edge for snapshot_axis mode
            if self.homing == "snapshot_axis":
                self.spawn_edge = kwargs.get("spawn_edge", getattr(self, "spawn_edge", None))

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

    def _update_homing_snapshot_axis(self, dt):
        """Lock perpendicular axis to player, move straight on spawn axis"""
        if not self.player_ref or not hasattr(self.player_ref, 'pos'):
            return

        if not self.locked:
            self.lock_timer += dt
            if self.lock_timer >= self.lock_delay:
                # Determine axis based on spawn edge and reposition
                if self.spawn_edge in ("top", "bottom"):
                    # Spawned from top/bottom → lock X axis, move on Y
                    self.pos.x = self.player_ref.pos.x
                    # Set velocity to move straight on Y axis
                    direction_y = 1 if self.spawn_edge == "top" else -1
                    self.velocity = pygame.Vector2(0, direction_y) * self.speed

                elif self.spawn_edge in ("left", "right"):
                    # Spawned from left/right → lock Y axis, move on X
                    self.pos.y = self.player_ref.pos.y
                    # Set velocity to move straight on X axis
                    direction_x = 1 if self.spawn_edge == "left" else -1
                    self.velocity = pygame.Vector2(direction_x, 0) * self.speed

                else:
                    # Fallback: no spawn_edge provided, behave like regular snapshot
                    to_player = self.player_ref.pos - self.pos
                    if to_player.length() > 0:
                        self.velocity = to_player.normalize() * self.speed

                self.locked = True