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
from src.core.runtime.game_settings import Display, Layers
from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import CollisionTags, LifecycleState, EntityCategory


class BaseItem(BaseEntity):
    """Base class for all collectible items."""

    def __init__(self, x, y, image=None, shape_data=None, draw_manager=None,
                 speed=50, despawn_y=None):
        """
        Initialize a base item entity.

        Args:
            x (float): Spawn X position.
            y (float): Spawn Y position.
            image (pygame.Surface, optional): Item sprite.
            shape_data (dict, optional): Shape rendering config.
            draw_manager: Reference to draw manager for shape optimization.
            speed (float): Downward movement speed (pixels/second).
            despawn_y (float, optional): Y coordinate to despawn at. Defaults to screen height.
        """
        super().__init__(x, y, image=image, shape_data=shape_data, draw_manager=draw_manager)

        self.speed = speed
        self.despawn_y = despawn_y if despawn_y is not None else Display.HEIGHT

        # Collision setup
        self.collision_tag = CollisionTags.PICKUP
        self.category = EntityCategory.PICKUP
        self.layer = Layers.ENEMIES  # Same layer as enemies for now

        # Hitbox scale (smaller than visual for easier collection)
        self._hitbox_scale = 0.8

        # Movement
        self.velocity = pygame.Vector2(0, self.speed)

    def update(self, dt: float):
        """Update item position and check for despawn."""
        if self.death_state != LifecycleState.ALIVE:
            return

        # Move downward
        self.pos += self.velocity * dt
        self.sync_rect()

        # Despawn if off-screen
        if self.rect.top > self.despawn_y:
            self.mark_dead(immediate=True)

    def draw(self, draw_manager):
        """Render the item sprite."""
        draw_manager.draw_entity(self, layer=self.layer)

    def on_collision(self, other):
        """Handle collision with player."""
        tag = getattr(other, "collision_tag", "unknown")

        if tag == "player":
            self.on_pickup(other)
            self.mark_dead(immediate=True)

    def on_pickup(self, player):
        """
        Override in subclasses to implement pickup effects.

        Args:
            player: Reference to player entity that collected this item.
        """
        print("Picked up item")