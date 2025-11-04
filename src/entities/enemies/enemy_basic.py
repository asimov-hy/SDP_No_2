"""
enemy_basic.py
--------------
Defines a simple downward-moving enemy for early gameplay testing.

Responsibilities
----------------
- Move straight down the screen at a constant speed.
- Reset to the top once off-screen.
- Serve as the baseline template for all other enemy types.
"""

from src.core.settings import Debug, Display
from src.entities.enemies.enemy import Enemy
from src.core.utils.debug_logger import DebugLogger

class EnemyBasic(Enemy):
    """Basic enemy that moves vertically downward and loops back to top."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image, speed=100, hp=1):
        """
        Initialize a basic enemy instance.

        Args:
            x (float): Spawn X position.
            y (float): Spawn Y position.
            image (pygame.Surface): Enemy sprite image.
            speed (float, optional): Movement speed in pixels/second.
            hp (int, optional): Enemy hit points.
        """
        super().__init__(x, y, image, speed=speed, hp=hp)

        if Debug.VERBOSE_ENTITY_INIT:
            DebugLogger.init(f"Spawned at ({x}, {y}) | Speed={speed}")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Move the enemy downward each frame, wrapping to the top when off-screen.

        Args:
            dt (float): Delta time (in seconds) since last frame.
        """
        if not self.alive:
            return

        self.rect.y += self.speed * dt

        # Destroy if the enemy moves beyond the bottom of the screen
        if self.rect.top > Display.HEIGHT:
            self.alive = False
            if Debug.VERBOSE_ENTITY_DEATH:
                DebugLogger.state(f"Destroyed (off-screen) at Y={self.rect.y:.1f}")