"""
base_item.py
------------
Base class for all collectible items in the game.

Responsibilities
----------------
- Handle spawning, movement, and collection behavior
- Provide hook for pickup effects (overridden in subclasses)
- Auto-despawn when off-screen
- Support both image and shape rendering
"""

import pygame
import random
import math
from src.core.runtime.game_settings import Display, Layers
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import LifecycleState
from src.entities.entity_types import CollisionTags, EntityCategory
from src.core.services.event_manager import get_events, ItemCollectedEvent
from src.entities.player.player_effects import apply_item_effects


class BaseItem(BaseEntity):
    """Base class for all collectible items."""

    __slots__ = (
        'item_data', 'speed', 'despawn_y', 'velocity',
        'lifetime', 'lifetime_timer', 'bounce_enabled'
    )

    __registry_category__ = "pickup"
    __registry_name__ = "default"

    def __init_subclass__(cls, **kwargs):
        """Auto-register item subclasses when they're defined."""
        super().__init_subclass__(**kwargs)

    def __init__(self, x, y, item_data=None, image=None, shape_data=None,
                 draw_manager=None, speed=500, despawn_y=None, lifetime=5.0, bounce=True):
        """
        Initialize a base item entity.

        Args:
            x (float): Spawn X position.
            y (float): Spawn Y position.
            item_data (dict): Item configuration from items.json
            image (pygame.Surface, optional): Item sprite.
            shape_data (dict, optional): Shape rendering config.
            draw_manager: Reference to draw manager for shape optimization.
            speed (float): Downward movement speed (pixels/second).
            despawn_y (float, optional): Y coordinate to despawn at. Defaults to screen height.
        """
        # Store item data first
        self.item_data = item_data or {}

        # Extract physics config from item_data
        physics = self.item_data.get("physics", {})
        velo_x = physics.get("velo_x", 0)
        velo_y = physics.get("velo_y", speed)
        hitbox_scale = physics.get("hitbox_scale", 0.5)

        # Build hitbox config
        hitbox_config = {'scale': hitbox_scale}

        super().__init__(x, y, image=image, shape_data=shape_data,
                         draw_manager=draw_manager, hitbox_config=hitbox_config)

        # Extract visual scale and apply to sprite
        BASE_W, BASE_H = (48, 48)

        if "size" in self.item_data:
            # JSON explicit pixel size override
            final_size = tuple(self.item_data["size"])
        else:
            # JSON scale or default scale (1.0 means 48x48)
            scale = self.item_data.get("scale", 1.0)
            final_size = (int(BASE_W * scale), int(BASE_H * scale))

        # Apply scaling once, always from raw sprite
        if self.image:
            self.image = pygame.transform.scale(self.image, final_size)
            self.rect = self.image.get_rect(center=(x, y))

        self.speed = velo_y
        self.despawn_y = despawn_y if despawn_y is not None else Display.HEIGHT

        # Collision setup
        self.collision_tag = CollisionTags.PICKUP
        self.category = EntityCategory.PICKUP
        self.layer = Layers.PICKUPS

        # Movement - use physics data
        self.velocity = pygame.Vector2(velo_x, velo_y)

        # Timer system
        self.lifetime = lifetime
        self.lifetime_timer = 0.0

        # Bouncing
        self.bounce_enabled = bounce
        if bounce:
            # Random initial direction
            angle = random.uniform(0, 360)
            self.velocity = pygame.Vector2(
                speed * math.cos(math.radians(angle)),
                speed * math.sin(math.radians(angle))
            )

    def update(self, dt: float):
        if self.death_state != LifecycleState.ALIVE:
            return

        # Timer despawn
        self.lifetime_timer += dt
        if self.lifetime_timer >= self.lifetime:
            self.mark_dead(immediate=True)
            return

        # Move
        self.pos.x += self.velocity.x * dt
        self.pos.y += self.velocity.y * dt

        # Bounce off screen edges
        if self.bounce_enabled:
            if self.pos.x <= 0 or self.pos.x >= Display.WIDTH:
                self.velocity.x *= -1  # Reflect X
            if self.pos.y <= 0 or self.pos.y >= Display.HEIGHT:
                self.velocity.y *= -1  # Reflect Y

        self.sync_rect()

    def draw(self, draw_manager):
        """Render the item sprite."""
        draw_manager.draw_entity(self, layer=self.layer)

    def get_effects(self) -> list:
        """Returns effects list from item_data."""
        return self.item_data.get("effects", [])

    def on_collision(self, other):
        """Handle collision with player."""
        tag = getattr(other, "collision_tag", "unknown")

        if tag == "player":
            # Apply effects directly to player
            apply_item_effects(other, self.get_effects())

            # Notify observers (achievements, ui, etc can subscribe)
            get_events().dispatch(ItemCollectedEvent(effects=self.get_effects()))

            # Legacy hook for subclasses (can be removed later)
            self.on_pickup(other)

            self.mark_dead(immediate=True)

    def on_pickup(self, player):
        """
        Override in subclasses to implement pickup effects.

        Args:
            player: Reference to player entity that collected this item.
        """
        print("Picked up item")

    # ===========================================================
    # Reset for Object Pooling
    # ===========================================================
    def reset(self, x, y, speed=None, despawn_y=None, color=None, size=None, **kwargs):
        """
        Reset item for object pooling reuse.

        Args:
            x: New X position
            y: New Y position
            speed: Optional new downward speed
            despawn_y: Optional new despawn threshold
            color: Optional new color (triggers sprite rebuild)
            size: Optional new size (triggers sprite rebuild)
            **kwargs: Additional parameters passed to BaseEntity.reset()
        """
        # Reset base entity state
        super().reset(x, y, **kwargs)

        # Reset timer
        self.lifetime_timer = 0.0

        # Update speed if provided
        if speed is not None:
            self.speed = speed
            self.velocity = pygame.Vector2(0, self.speed)

        # Update despawn threshold if provided
        if despawn_y is not None:
            self.despawn_y = despawn_y

        # Rebuild sprite if size/color changed
        if (color is not None or size is not None) and self.draw_manager:
            new_color = color if color is not None else self.shape_data.get("color", (0, 255, 0))
            new_size = size if size is not None else self.shape_data.get("size", (24, 24))
            shape_type = self.shape_data.get("type", "circle")

            # Update shape_data
            self.shape_data = {
                "type": shape_type,
                "color": new_color,
                "size": new_size,
                "kwargs": self.shape_data.get("kwargs", {})
            }

            # Rebuild sprite
            self.refresh_sprite(new_color=new_color, shape_type=shape_type, size=new_size)

        # Sync rect to new position
        self.sync_rect()
