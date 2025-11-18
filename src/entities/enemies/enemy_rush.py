import pygame
import os
from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_registry import EntityRegistry


class EnemyRush(BaseEnemy):
    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "rush"

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, direction=(0, 1), speed=None, health=None,
                 scale=None, draw_manager=None, score=None,
                 approach_duration=None, dash_speed=None, **kwargs):
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
        defaults = EntityRegistry.get_data("enemy", "rush")

        # Apply overrides or use defaults
        speed = speed if speed is not None else defaults.get("speed", 150)
        health = health if health is not None else defaults.get("hp", 1)
        scale = scale if scale is not None else defaults.get("scale", 1.0)
        score = score if score is not None else defaults.get("score", 50)

        self.approach_duration = approach_duration if approach_duration is not None else defaults.get("approach_duration", 1.0)
        self.dash_speed = dash_speed if dash_speed is not None else defaults.get("dash_speed", 300.0)
        self._approach_elapsed = 0.0
        self.behavior_state = "approach"

        image_path = defaults.get("image", "assets/images/sprites/enemies/missile.png")
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
            hitbox_config=hitbox_config,
            score=score
        )

        # Store exp value for when enemy dies
        self.exp_value = defaults.get("exp", 0)

        DebugLogger.init(
            f"Spawned EnemyRush at ({x}, {y}) | Speed={speed}",
            category="entity_spawn"
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
        # DebugLogger.state(f"EnemyRush approach | speed={self.speed} | velocity={self.velocity}",
        #                   category="entity_logic")

        if self.behavior_state == "approach":
            self._approach_elapsed += dt
            if self._approach_elapsed >= self.approach_duration:
                self.speed = self.dash_speed
                self.velocity = self.velocity.normalize() * self.dash_speed
                self.update_rotation()
                self.behavior_state = "dashing"

        super().update(dt)

    def reset(self, x, y, direction=(0, 1), speed=None, health=None, scale=None, score=None, approach_duration=None, dash_speed=None, **kwargs):
        # Load defaults from JSON (correct enemy type: "rush")
        defaults = EntityRegistry.get_data("enemy", "rush")

        speed = speed if speed is not None else defaults.get("speed", 150)
        health = health if health is not None else defaults.get("hp", 1)
        scale = scale if scale is not None else defaults.get("scale", 1.0)
        image_path = defaults.get("image")
        hitbox_scale = defaults.get("hitbox", {}).get("scale", 0.85)
        score = score if score is not None else defaults.get("score", 50)

        self.approach_duration = approach_duration if approach_duration is not None else defaults.get("approach_duration", 1.0)
        self.dash_speed = dash_speed if dash_speed is not None else defaults.get("dash_speed", 300.0)
        self._approach_elapsed = 0.0
        self.behavior_state = "approach"

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
            hitbox_scale=hitbox_scale,
            score=score
        )

        DebugLogger.system(
            f"reset EnemyRush at ({x}, {y}) | Speed={speed}",
            category="entity_spawn"
        )
