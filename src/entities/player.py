import pygame
from src.core.settings import PLAYER_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT

class Player:
    def __init__(self, x, y, image):
        self.image = image
        self.rect = self.image.get_rect(center=(x, y))

        # Future extensions
        self.velocity = pygame.Vector2(0, 0)
        self.health = 3
        self.alive = True

    def update(self, dt, move_vec):
        """Update player position based on input vector."""
        if not self.alive:
            return

        # Apply normalized movement vector
        if move_vec.length_squared() > 0:
            self.velocity = move_vec * PLAYER_SPEED * dt
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
        else:
            self.velocity.update(0, 0)

        # Keep player inside screen bounds
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))

    # No draw() method — DrawManager handles rendering
