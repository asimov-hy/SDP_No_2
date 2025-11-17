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
from src.entities.base_entity import BaseEntity
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
                 scale=None, draw_manager=None, **kwargs):
        """
        Args:
            x, y: Spawn position
            direction: Tuple (dx, dy) for movement direction
            speed: Pixels per second (override, or use JSON default)
            health: HP before death (override, or use JSON default)
            size: Size override (or use JSON default)
            draw_manager: Required for sprite loading
        """

        # Load defaults from JSON
        defaults = EntityRegistry.get_data("enemy", "straight")

        # Apply overrides or use defaults
        speed = speed if speed is not None else defaults.get("speed", 200)
        health = health if health is not None else defaults.get("hp", 1)
        scale = scale if scale is not None else defaults.get("scale", 1.0)

        image_path = defaults.get("image", "assets/images/characters/enemies/missile.png")
        hitbox_config = defaults.get("hitbox", {})

        # Create sprite
        if draw_manager is None:
            raise ValueError("EnemyStraight requires draw_manager for sprite loading")

        # Load and scale image using helper
        img = BaseEntity.load_and_scale_image(image_path, scale)

        super().__init__(
            x, y,
            image=img,
            draw_manager=draw_manager,
            speed=speed,
            health=health,
            direction=direction,
            spawn_edge=kwargs.get("spawn_edge", None),
            hitbox_config=hitbox_config
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

    def reset(self, x, y, direction=(0, 1), speed=None, health=None, scale=None, **kwargs):
        # Load defaults from JSON (same as __init__)
        defaults = EntityRegistry.get_data("enemy", "straight")

        speed = speed if speed is not None else defaults.get("speed", 200)
        health = health if health is not None else defaults.get("hp", 1)
        scale = scale if scale is not None else defaults.get("scale", 1.0)
        image_path = defaults.get("image")
        hitbox_scale = defaults.get("hitbox", {}).get("scale", 0.85)

        # Reload and rescale image if using image mode
        if image_path and os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()

            # Apply scale
            if isinstance(scale, (int, float)):
                new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
            elif isinstance(scale, (list, tuple)) and len(scale) == 2:
                new_size = (int(img.get_width() * scale[0]), int(img.get_height() * scale[1]))
            else:
                new_size = img.get_size()

            self.image = pygame.transform.scale(img, new_size)
            self.rect = self.image.get_rect(center=(x, y))
            self._base_image = self.image

        # Update exp value in case it changed
        self.exp_value = defaults.get("exp", 0)

        # Call super to reset position/state
        super().reset(
            x, y,
            direction=direction,
            speed=speed,
            health=health,
            spawn_edge=kwargs.get("spawn_edge"),
            hitbox_scale=hitbox_scale
        )
