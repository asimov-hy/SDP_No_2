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

from src.core.game_settings import Debug, Display
from src.entities.enemies.base_enemy import BaseEnemy
from src.core.utils.debug_logger import DebugLogger


class EnemyStraight(BaseEnemy):
    """Simple enemy that moves vertically downward and disappears when off-screen."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image, speed=100, hp=1):
        """
        Initialize a straight-moving enemy.

        Args:
            x (float): Spawn X position.
            y (float): Spawn Y position.
            image (pygame.Surface): Enemy sprite image.
            speed (float, optional): Movement speed in pixels/second.
            hp (int, optional): Enemy hit points.
        """
        super().__init__(x, y, image, speed=speed, hp=hp)

        DebugLogger.init(
            f"Spawned EnemyStraight at ({x}, {y}) | Speed={speed}",
            category="effects"
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
        if not self.alive:
            return

        # Move downward
        self.pos.y += self.speed * dt
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

        # Update hitbox
        if self.hitbox:
            self.hitbox.update()

        # Destroy when off-screen
        if self.pos.y > Display.HEIGHT:
            self.alive = False

            DebugLogger.state(
                f"{type(self).__name__} off-screen at y={self.pos.y:.1f}",
                category="effects"
            )
