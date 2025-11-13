"""
base_bullet.py
--------------
Defines the base Bullet class providing shared logic for all bullet types.

Responsibilities
----------------
- Define position, velocity, and lifespan handling.
- Provide update and draw methods for derived bullet classes.
- Manage per-bullet motion and collision.
- Defer off-screen cleanup and pooling to BulletManager.
"""

import pygame
from src.core.runtime import game_settings
from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import LifecycleState, EntityCategory


class BaseBullet(BaseEntity):
    """Base class for all bullet entities_animation."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, pos, vel, image=None, color=(255, 255, 255),
                 radius=3, owner="player", damage=1, hitbox_scale=0.9, draw_manager=None):
        """
        Initialize the base bullet entity.

        Args:
            pos (tuple[float, float]): Starting position.
            vel (tuple[float, float]): Velocity vector.
            image (pygame.Surface): Optional sprite image.
            color (tuple[int, int, int]): RGB color (used if no image).
            radius (int): Circle radius when using shape rendering.
            owner (str): Bullet origin ('player' or 'enemy').
            damage (int): Damage value applied on collision.
            hitbox_scale (float): Scale factor for hitbox relative to sprite.
            draw_manager: Optional DrawManager for shape prebaking.
        """
        radius = max(1, radius)
        size = (radius * 2, radius * 2)

        # Build shape_data dict if no image
        shape_data = None
        if image is None:
            shape_data = {
                "type": "circle",
                "color": color,
                "size": size
            }

        super().__init__(
            x=pos[0],
            y=pos[1],
            image=image,
            shape_data=shape_data,
            draw_manager=draw_manager
        )

        # Core attributes
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.death_state = LifecycleState.ALIVE
        self.owner = owner
        self.radius = radius
        self.damage = damage

        # Collision setup
        self.collision_tag = f"{owner}_bullet"
        self.category = EntityCategory.PROJECTILE
        self.hitbox_scale = hitbox_scale
        self.layer = game_settings.Layers.BULLETS

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Base per-frame bullet logic.

        Responsibilities:
            - Move the bullet according to its velocity.
            - Sync its rect and hitbox.
            - (Offscreen cleanup handled by BulletManager.)
        """
        if self.death_state >= LifecycleState.DEAD:
            return

        # Motion update
        self.pos += self.vel * dt
        self.rect.center = self.pos

    # ===========================================================
    # Collision Handling
    # ===========================================================
    def on_collision(self, target):
        """
        Entry point for collision events from CollisionManager.

        Args:
            target (BaseEntity): The entity that this bullet collided with.
        """
        if self.death_state >= LifecycleState.DEAD or target is self:
            return
        self.handle_collision(target)

    def handle_collision(self, target):
        """
        Default bullet behavior upon collision.

        Responsibilities:
            - Mark bullet inactive (destroyed).
            - Log the event.

        Subclasses can override to add piercing, explosion, or
        special animation_effects upon impact.
        """
        self.death_state = LifecycleState.DEAD
        DebugLogger.state(
            f"{type(self).__name__} hit {type(target).__name__} → destroyed",
            category="collision"
        )

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render the bullet on screen.

        Draws either an image or fallback circle based on render mode.
        """
        super().draw(draw_manager)
