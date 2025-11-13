import pygame
from src.entities.enemies.base_enemy import BaseEnemy
from src.core.debug.debug_logger import DebugLogger


class EnemyRush(BaseEnemy):
    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=100, health=1,
                 size=50, color=(214, 150, 39), draw_manager=None,
                 approach_duration: float = 1, dash_speed: float = 300):
        # Create triangle sprite
        if draw_manager is None:
            raise ValueError("EnemyRush requires draw_manager for triangle creation")

        triangle_image = draw_manager.create_triangle(size, color, pointing="up")

        # Initialize base enemy
        super().__init__(x, y, triangle_image, speed, health)

        self.direction = direction
        self.velocity = pygame.Vector2(direction).normalize() * speed
        self.dash_speed = dash_speed
        self.update_rotation()

        self.approach_duration = approach_duration
        self._approach_elapsed = 0.0
        self.behavior_state = "approach"

        DebugLogger.init(
            f"Spawned EnemyRush at ({x}, {y}) | approach={approach_duration}s dash_speed={dash_speed}",
            category="animation_effects"
        )

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        if self.behavior_state == "approach":
            self._approach_elapsed += dt
            if self._approach_elapsed >= self.approach_duration:
                self.velocity = pygame.Vector2(self.direction).normalize()  * self.dash_speed
                self.update_rotation()

                self.speed = self.dash_speed
                self.behavior_state = "dashing"

        super().update(dt)

    def reset(self, x, y, direction=(0, 1), speed=100, health=1, size=50, color=(214, 150, 39),
              approach_duration: float = 1, dash_speed: float = 300, **kwargs):
        """Reset enemy and rush-specific behavior_state."""
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
        self.approach_duration = approach_duration
        self.dash_speed = dash_speed
        self._approach_elapsed = 0.0
        self.behavior_state = "approach"

        # Reset rotation state
        self.rotation_angle = 0

        # Force immediate rotation update to match velocity
        self.update_rotation()

from src.entities.entity_registry import EntityRegistry
EntityRegistry.register("enemy", "rush", EnemyRush)
