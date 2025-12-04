"""
Mine hazard spawned during boss charge attack.
"""
import pygame
import math
from src.entities.base_hazard import BaseHazard, HazardState
from src.entities.base_entity import BaseEntity


class MineHazard(BaseHazard):
    """
    Proximity mine that telegraphs, then explodes on contact.
    """

    def __init__(self, x, y, draw_manager=None, **kwargs):
        super().__init__(
            x, y,
            telegraph_time=0.3,
            active_time=5.0,
            draw_manager=draw_manager,
            **kwargs
        )

        # Visual properties
        self.radius = 20
        self.damage = 15

        # Pulsing animation
        self.pulse_timer = 0.0
        self.pulse_speed = 3.0

        # Create visual
        self._create_image()

    def _create_image(self):
        """Create mine sprite."""
        size = self.radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

    def update(self, dt):
        """Update mine state and visuals."""
        super().update(dt)

        self.pulse_timer += dt

        # Redraw based on state
        self._update_visual()

    def _update_visual(self):
        """Update visual based on hazard state."""
        self.image.fill((0, 0, 0, 0))

        # Pulsing effect
        pulse = abs(math.sin(self.pulse_timer * self.pulse_speed))

        if self.hazard_state == HazardState.TELEGRAPH:
            # Yellow warning pulse
            alpha = int(100 + 155 * pulse)
            color = (255, 255, 0, alpha)
            radius = int(self.radius * (0.5 + 0.3 * pulse))

        elif self.hazard_state == HazardState.ACTIVE:
            # Red danger
            alpha = int(150 + 105 * pulse)
            color = (255, 50, 0, alpha)
            radius = self.radius

        else:  # FADEOUT
            # Fade out
            alpha = int(255 * (1.0 - self.state_timer / self.fadeout_time))
            color = (255, 100, 0, alpha)
            radius = int(self.radius * 1.5)

        center = (self.radius, self.radius)
        pygame.draw.circle(self.image, color, center, radius)

        # Core dot
        if self.hazard_state != HazardState.FADEOUT:
            pygame.draw.circle(self.image, (50, 50, 50), center, 3)