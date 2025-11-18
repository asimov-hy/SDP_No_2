import pygame
from src.entities.enemies.base_enemy import BaseEnemy
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_types import EntityCategory


class EnemyMultipleShot(BaseEnemy):
    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "multiple_shot"

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=70, health=3,
                 size=50, color=(96, 130, 120), draw_manager=None, score=100, **kwargs):
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
            raise ValueError("EnemyMultipleShot requires draw_manager for triangle creation")

        norm_size = (size, size) if isinstance(size, int) else size

        shape_data = {
            "type": "triangle",
            "size": norm_size,
            "color": color,
            "kwargs": {"pointing": "up", "equilateral": True}
        }
        super().__init__(
            x, y,
            shape_data=shape_data,
            draw_manager=draw_manager,
            speed=speed,
            health=health,
            direction=direction,
            spawn_edge=kwargs.get("spawn_edge", None),
            score=score
        )

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

    def reset(self, x, y, direction=(0, 1), speed=70, health=3, size=50, color=(96, 130, 120), score=100, **kwargs):
        # Only regenerate if visuals changed
        norm_size = (size, size) if isinstance(size, int) else size

        # Initialize shape_data if first use, or check if regeneration needed
        needs_regeneration = (
                not hasattr(self, 'shape_data') or
                norm_size != self.shape_data.get("size") or
                color != self.shape_data.get("color")
        )

        if needs_regeneration:
            self.shape_data = {
                "type": "triangle",
                "size": norm_size,
                "color": color,
                "kwargs": {"pointing": "up", "equilateral": True}
            }
            if self.draw_manager:
                self.refresh_sprite(new_color=color, shape_type="triangle", size=norm_size)
                self._base_image = self.image

        # Call super ONCE at the end
        super().reset(
            x, y,
            direction=direction,
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge"),
            score=score
        )

from src.entities.entity_registry import EntityRegistry
EntityRegistry.register("enemy", "multiple_shot", EnemyMultipleShot)
