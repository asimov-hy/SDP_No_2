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

from src.core.settings import Debug, Display
from src.entities.enemies.enemy_base import EnemyBase
from src.core.utils.debug_logger import DebugLogger


class EnemyStraight(EnemyBase):
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

        if Debug.VERBOSE_ENTITY_INIT:
            DebugLogger.init(f"Spawned EnemyStraight at ({x}, {y}) | Speed={speed}")

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

        self.rect.y += self.speed * dt

        # Destroy once off-screen
        if self.rect.top > Display.HEIGHT:
            self.alive = False
            if Debug.VERBOSE_ENTITY_DEATH:
                DebugLogger.state(f"Destroyed (off-screen) at Y={self.rect.y:.1f}")
