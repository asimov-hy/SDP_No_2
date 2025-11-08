"""
bullet_base.py
--------------
Defines the base Bullet class providing shared logic for all bullets types.

Responsibilities
----------------
- Define position, velocity, and lifetime handling.
- Provide update and draw methods for derived bullets classes.
- Handle off-screen cleanup and base rendering logic.
"""

import pygame
from src.core import settings


class BulletBase:
    """Base class for all bullets entities."""

    def __init__(self, pos, vel, image=None, color=(255, 255, 255), radius=3, owner="player"):
        """
        Initialize the base bullets.

        Args:
            pos (tuple[float, float]): Starting position.
            vel (tuple[float, float]): Velocity vector.
            image (pygame.Surface): Optional image for rendering.
            color (tuple[int, int, int]): RGB color for fallback rendering.
            radius (int): Hitbox radius when no image is used.
            owner (str): Entity type that fired the bullets ('player' or 'enemy').
        """
        # -------------------------------------------------------
        # Core Properties
        # -------------------------------------------------------
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.alive = True
        self.owner = owner
        self.image = image
        self.color = color
        self.radius = radius

        # -------------------------------------------------------
        # Rect for collision & rendering
        # -------------------------------------------------------
        if self.image:
            self.rect = self.image.get_rect(center=pos)
        else:
            self.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            self.rect.center = pos

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt):
        """
        Update bullets position and check screen bounds.

        Responsibilities:
            - Move bullets according to velocity and delta time.
            - Deactivate when moving outside screen area.
        """
        self.pos += self.vel * dt
        self.rect.center = self.pos

        # Off-screen cleanup (with buffer)
        if (
                self.pos.y < -50 or self.pos.y > settings.Display.HEIGHT + 50 or
                self.pos.x < -50 or self.pos.x > settings.Display.WIDTH + 50
        ):
            self.alive = False

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, surface):
        """
        Render the bullets to the given surface.

        Responsibilities:
            - Draw image if available.
            - Otherwise, render a simple circle.
        """
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.circle(surface, self.color, self.rect.center, self.radius)
