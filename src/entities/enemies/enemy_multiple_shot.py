import pygame
from src.entities.enemies.base_enemy import BaseEnemy
from src.core.debug.debug_logger import DebugLogger


class EnemyMultipleShot(BaseEnemy):
    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=70, health=3,
                 size=50, color=(96, 130, 120), draw_manager=None, score=100):
        """
        Args:
            x, y: Spawn position
            direction: Tuple (dx, dy) for movement direction
            speed: Pixels per second
            health: HP before death
            size: Triangle size (equilateral if int, else (w, h))
            color: RGB tuple
            draw_manager: Required for triangle creation
        """
        # Create triangle sprite
        if draw_manager is None:
            raise ValueError("EnemyStraight requires draw_manager for triangle creation")

        triangle_image = draw_manager.create_triangle(size, color, pointing="up")

        # Initialize base enemy
        super().__init__(x, y, triangle_image, speed, health, score)

        # Set velocity from direction
        self.velocity = pygame.Vector2(direction).normalize() * self.speed

        DebugLogger.init(
            f"Spawned EnemyStraight at ({x}, {y}) | Speed={speed}",
            category="animation_effects"
        )

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Move the enemy downward each frame and mark as destroyed once off-screen.

        Args:
            dt (float): Delta time (in seconds) since last frame.
        """
        super().update(dt)

    def reset(self, x, y, direction=(0, 1), speed=200, health=1, size=50, color=(255, 0, 0), **kwargs):
        """Reset straight enemy with new parameters."""
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

from src.entities.entity_registry import EntityRegistry
EntityRegistry.register("enemy", "multiple_shot", EnemyMultipleShot)
