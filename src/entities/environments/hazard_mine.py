"""
Mine hazard spawned during boss charge attack.
"""
import pygame
import math
from src.entities.environments.base_hazard import BaseHazard, HazardState
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory


class MineHazard(BaseHazard):
    """
    Proximity mine that telegraphs, then explodes on contact.
    """

    __registry_category__ = EntityCategory.HAZARD
    __registry_name__ = "mine"

    def __init__(self, x, y, draw_manager=None, telegraph_time=0.3, active_time=5.0, **kwargs):
        super().__init__(
            x, y,
            telegraph_time=telegraph_time,
            active_time=active_time,
            draw_manager=draw_manager,
            **kwargs
        )

        # Visual properties
        self.radius = 200
        self.damage = 15

        # Load sprite
        self._base_image = self._load_image()
        self.image = self._base_image.copy()
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))
        self._update_visual()

    def _load_image(self):
        """Load mine sprite from file."""
        img = BaseEntity.load_and_scale_image(
            "assets/images/sprites/projectiles/land_mine.png",
            scale=1.0
        )
        if img:
            # Update radius based on image size
            self.radius = max(img.get_width(), img.get_height()) // 2
            return img

        # Fallback: draw circle
        size = self.radius * 2
        fallback = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(fallback, (255, 100, 0), (self.radius, self.radius), self.radius)
        return fallback

    def update(self, dt):
        """Update mine state and visuals."""
        super().update(dt)
        self._update_visual()

    def _update_visual(self):
        """Update visual based on hazard state."""
        # Start fresh from base image
        self.image = self._base_image.copy()

        if self.hazard_state == HazardState.TELEGRAPH:
            # Faint -> gradually becoming visible
            progress = self.state_timer / self.telegraph_time
            alpha = int(50 + 150 * progress)  # 50 -> 200
            self.image.set_alpha(alpha)

        elif self.hazard_state == HazardState.ACTIVE:
            # Fully solid
            self.image.set_alpha(255)

        else:  # FADEOUT
            # Fade out
            progress = self.state_timer / self.fadeout_time
            alpha = int(255 * (1.0 - progress))
            self.image.set_alpha(alpha)