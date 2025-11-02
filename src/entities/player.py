"""
player.py
---------
Defines the Player entity and its core update logic.

Responsibilities
----------------
- Maintain player position, movement, and health state.
- Update position based on input direction and delta time.
- Stay within screen boundaries.
- (Optional) Integrate with DebugLogger for movement and state tracking.
"""
import pygame
from src.core.settings import PLAYER_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.utils.debug_logger import DebugLogger

class Player:
    """Represents the controllable player entity."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image):
        """
        Initialize the player with position and sprite.

        Args:
            x (float): Initial x-coordinate.
            y (float): Initial y-coordinate.
            image (pygame.Surface): The sprite surface for rendering.
        """
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))

        # Future extensions
        self.velocity = pygame.Vector2(0, 0)
        self.health = 3
        self.alive = True
        DebugLogger.init("Player", f"Initialized at position ({x}, {y})")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt, move_vec):
        """
        Update player position based on input vector and time delta.

        Args:
            dt (float): Time elapsed since last frame.
            move_vec (pygame.Vector2): Normalized movement direction.
        """
        if not self.alive:
            return

        # Apply normalized movement vector
        if move_vec.length_squared() > 0:
            self.velocity = move_vec * PLAYER_SPEED * dt
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
            # DebugLogger.state("Player", f"Moved to ({self.rect.x:.1f}, {self.rect.y:.1f}) | Velocity: {self.velocity}")
        else:
            self.velocity.update(0, 0)

        # Keep player inside screen bounds
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        # DebugLogger.state("Player", "Position clamped within screen bounds")