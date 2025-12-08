"""
bullet_bouncing.py
------------------
Bullet that bounces off screen edges for a set duration.
"""

from src.entities.bullets.base_bullet import BaseBullet
from src.entities.entity_types import EntityCategory
from src.entities.entity_state import LifecycleState
from src.core.runtime.game_settings import Display


class BouncingBullet(BaseBullet):
    """Bullet that bounces off screen edges until max bounces reached."""

    __registry_category__ = EntityCategory.PROJECTILE
    __registry_name__ = "bouncing"

    __slots__ = ("bounce_count", "max_bounces", "margin")

    def __init__(self, *args, max_bounces=3, **kwargs):
        """
        Args:
            max_bounces: How many times bullet can bounce before expiring
        """
        super().__init__(*args, **kwargs)
        self.bounce_count = 0
        self.max_bounces = max_bounces
        self.margin = 10  # Bounce margin from screen edge

    def update(self, dt: float):
        """Move and bounce off screen edges."""
        if self.death_state >= LifecycleState.DEAD:
            return

        # Move
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

        # Bounce off edges
        bounced = False

        if self.pos.x <= self.margin:
            self.pos.x = self.margin
            self.vel.x = abs(self.vel.x)
            bounced = True
        elif self.pos.x >= Display.WIDTH - self.margin:
            self.pos.x = Display.WIDTH - self.margin
            self.vel.x = -abs(self.vel.x)
            bounced = True

        if self.pos.y <= self.margin:
            self.pos.y = self.margin
            self.vel.y = abs(self.vel.y)
            bounced = True
        elif self.pos.y >= Display.HEIGHT - self.margin:
            self.pos.y = Display.HEIGHT - self.margin
            self.vel.y = -abs(self.vel.y)
            bounced = True

        # Count bounce and check limit
        if bounced:
            self.bounce_count += 1
            if self.bounce_count >= self.max_bounces:
                self.death_state = LifecycleState.DEAD
                return

        # Rotate to face movement direction
        self.update_rotation(velocity=self.vel)
        self.sync_rect()

    def is_offscreen(self) -> bool:
        """Bouncing bullets never go offscreen - they expire by lifetime."""
        return False
