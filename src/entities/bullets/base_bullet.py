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
from src.core.runtime.game_settings import Bounds
from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import LifecycleState, InteractionState
from src.entities.entity_types import EntityCategory, CollisionTags
from src.systems.entity_management.entity_registry import EntityRegistry


class BaseBullet(BaseEntity):
    """Base class for all bullet entities_animation."""

    # Add slots for bullet-specific attributes
    __slots__ = ('vel', 'owner', 'radius', 'damage', 'state')

    _cached_defaults = None

    def __init_subclass__(cls, **kwargs):
        """Auto-register bullet subclasses when they're defined."""
        super().__init_subclass__(**kwargs)
        EntityRegistry.auto_register(cls)

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, pos, vel, image=None, color=None,
                 radius=None, owner="player", damage=None, hitbox_scale=None, draw_manager=None):
        """
        Initialize the base bullet entity.

        Args:
            pos (tuple[float, float]): Starting position.
            vel (tuple[float, float]): Velocity vector.
            image (pygame.Surface): Optional sprite image (overrides JSON).
            color (tuple[int, int, int]): RGB color (override, or use JSON default).
            radius (int): Circle radius (override, or use JSON default).
            owner (str): Bullet origin ('player' or 'enemy').
            damage (int): Damage value (override, or use JSON default).
            hitbox_scale (float): Hitbox scale (override, or use JSON default).
            draw_manager: Optional DrawManager for shape prebaking.
        """

        # Load defaults from JSON
        if BaseBullet._cached_defaults is None:
            BaseBullet._cached_defaults = EntityRegistry.get_data("projectile", "straight")
        defaults = BaseBullet._cached_defaults

        # Apply overrides or use defaults
        damage = damage if damage is not None else defaults.get("damage", 1)
        radius = radius if radius is not None else defaults.get("radius", 3)
        color = tuple(color) if color is not None else tuple(defaults.get("color", [255, 255, 255]))
        hitbox_config = defaults.get("hitbox", {})

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
            draw_manager=draw_manager,
            hitbox_config=hitbox_config
        )

        # Core attributes
        self.vel = pygame.Vector2(vel)
        self.death_state = LifecycleState.ALIVE
        self.state = InteractionState.DEFAULT
        self.owner = owner
        self.radius = radius
        self.damage = damage

        # Collision setup
        self.collision_tag = CollisionTags.PLAYER_BULLET if owner == "player" else CollisionTags.ENEMY_BULLET
        self.category = EntityCategory.PROJECTILE
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

        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

        # Sync its rect and hitbox using the inherited helper method
        self.sync_rect()

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
    # Bounds & Margin System
    # ===========================================================
    def get_cleanup_margin(self):
        """
        Override cleanup margin based on bullet owner.
        Player bullets use smaller margin, enemy bullets travel further offscreen.
        """
        if self.owner == "player":
            return Bounds.BULLET_PLAYER_MARGIN
        else:
            return Bounds.BULLET_ENEMY_MARGIN

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render the bullet on screen.

        Draws either an image or fallback circle based on render mode.
        """
        super().draw(draw_manager)

    # ===========================================================
    # Reset for Object Pooling
    # ===========================================================
    def reset(self, pos, vel, color=None, radius=None, owner=None, damage=None, **kwargs):
        """
        Reset bullet for object pooling reuse.

        Args:
            pos: New position (x, y) tuple
            vel: New velocity (dx, dy) tuple
            color: Optional new color (triggers sprite rebuild)
            radius: Optional new radius (triggers sprite rebuild)
            owner: New owner ("player" or "enemy")
            damage: New damage value
            **kwargs: Additional parameters passed to BaseEntity.reset()
        """
        # Reset base entity state
        super().reset(pos[0], pos[1], **kwargs)

        # Reset position and velocity
        self.pos.update(pos)
        self.vel.update(vel)

        # Update owner if provided
        if owner is not None:
            self.owner = owner
            self.collision_tag = CollisionTags.PLAYER_BULLET if owner == "player" else CollisionTags.ENEMY_BULLET

        # Update damage if provided
        if damage is not None:
            self.damage = damage

        # Rebuild sprite if size/color changed
        if (color is not None or radius is not None) and self.draw_manager:
            new_radius = radius if radius is not None else self.radius
            new_color = color if color is not None else self.shape_data.get("color", (255, 255, 255))

            # Update stored properties
            self.radius = new_radius
            size = (new_radius * 2, new_radius * 2)

            # Update shape_data
            self.shape_data = {
                "type": "circle",
                "color": new_color,
                "size": size
            }

            # Rebuild sprite
            self.refresh_sprite(new_color=new_color, size=size)

        # Sync rect to new position
        self.sync_rect()
