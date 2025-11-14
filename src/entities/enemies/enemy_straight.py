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


class EnemyStraight(BaseEnemy):
    """Simple enemy that moves vertically downward and disappears when off-screen."""

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "straight"

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=200, health=1,
                 size=50, color=(255, 0, 0), draw_manager=None, **kwargs):
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
            spawn_edge=kwargs.get("spawn_edge", None)
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

    def reset(self, x, y, direction=(0, 1), speed=200, health=1, size=50, color=(255, 0, 0), **kwargs):
        """Reset straight enemy with new parameters."""
        # Regenerate sprite BEFORE calling super().reset()
        norm_size = (size, size) if isinstance(size, int) else size

        # Update shape_data for new size/color
        self.shape_data = {
            "type": "triangle",
            "size": norm_size,
            "color": color,
            "kwargs": {"pointing": "up", "equilateral": True}
        }

        # Rebuild image if draw_manager available
        if self.draw_manager:
            self.refresh_sprite(new_color=color, shape_type="triangle", size=norm_size)
            self._base_image = self.image

        # Call super AFTER image is ready
        super().reset(
            x, y,
            direction=direction,
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge")
        )
