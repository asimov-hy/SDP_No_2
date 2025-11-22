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

from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory
from src.core.debug.debug_logger import DebugLogger
from src.systems.entity_management.entity_registry import EntityRegistry


class EnemyStraight(BaseEnemy):
    """Simple enemy that moves vertically downward and disappears when off-screen."""

    __slots__ = ()

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "straight"
    _cached_defaults = None

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
        if EnemyStraight._cached_defaults is None:
            EnemyStraight._cached_defaults = EntityRegistry.get_data("enemy", "straight")
        defaults = EnemyStraight._cached_defaults

        # Apply overrides or use defaults
        speed = speed if speed is not None else defaults.get("speed", 200)
        health = health if health is not None else defaults.get("hp", 1)
        scale = scale if scale is not None else defaults.get("scale", 0.1)

        image_path = defaults.get("image", "assets/images/sprites/enemies/missile.png")
        hitbox_config = defaults.get("hitbox", {})

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

        # Load death frames AFTER super().__init__
        death_frame_paths = defaults.get("death_frames", [])

        # FIX: Use a specific 'death_scale' if provided, otherwise default to
        death_scale = defaults.get("death_scale", scale * 1.5)

        if death_frame_paths:
            self._death_frames = self.load_animation_frames(death_frame_paths, death_scale)

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
        defaults = EnemyStraight._cached_defaults

        speed = speed if speed is not None else defaults.get("speed", 200)
        health = health if health is not None else defaults.get("hp", 1)
        scale = scale if scale is not None else defaults.get("scale", 0.1)
        image_path = defaults.get("image")
        hitbox_scale = defaults.get("hitbox", {}).get("scale", 0.85)

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

        # Reload and rescale image if using image mode
        if image_path:
            self._reload_image_cached(image_path, scale)
