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
import os
from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.entity_types import EntityCategory
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_registry import EntityRegistry


class EnemyStraight(BaseEnemy):
    """Simple enemy that moves vertically downward and disappears when off-screen."""

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "straight"

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=None, health=None,
                 size=None, draw_manager=None, **kwargs):
        """
        Args:
            x, y: Spawn position
            direction: Tuple (dx, dy) for movement direction
            speed: Pixels per second (override, or use JSON default)
            health: HP before death (override, or use JSON default)
            size: Size override (or use JSON default)
            draw_manager: Required for sprite loading
        """
        from src.entities.entity_registry import EntityRegistry
        import os

        # Load defaults from JSON
        defaults = EntityRegistry.get_data("enemy", "straight")

        # Apply overrides or use defaults
        speed = speed if speed is not None else defaults.get("speed", 200)
        health = health if health is not None else defaults.get("hp", 1)
        size = size if size is not None else defaults.get("size", 48)
        image_path = defaults.get("image", "assets/images/characters/enemies/missile.png")
        hitbox_scale = defaults.get("hitbox", {}).get("scale", 0.85)

        # Create sprite
        if draw_manager is None:
            raise ValueError("EnemyStraight requires draw_manager for sprite loading")

        norm_size = (size, size) if isinstance(size, int) else size

        # Load image or use fallback shape
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            img = pygame.transform.scale(img, norm_size)

            super().__init__(
                x, y,
                image=img,
                draw_manager=draw_manager,
                speed=speed,
                health=health,
                direction=direction,
                spawn_edge=kwargs.get("spawn_edge", None),
                hitbox_scale=hitbox_scale
            )
        else:
            # Fallback to shape
            shape_data = {
                "type": "circle",
                "color": defaults.get("color", [255, 0, 0]),
                "size": norm_size
            }

            super().__init__(
                x, y,
                shape_data=shape_data,
                draw_manager=draw_manager,
                speed=speed,
                health=health,
                direction=direction,
                spawn_edge=kwargs.get("spawn_edge", None),
                hitbox_scale=hitbox_scale
            )

        # Store exp value for when enemy dies
        self.exp_value = defaults.get("exp", 0)

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
            spawn_edge=kwargs.get("spawn_edge")
        )
