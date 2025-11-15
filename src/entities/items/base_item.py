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
from src.entities.entity_state import LifecycleState
from src.entities.entity_types import CollisionTags, EntityCategory
from src.entities.entity_registry import EntityRegistry
from src.core.services.event_manager import EVENTS, ItemCollectedEvent
from src.entities.player.player_effects import apply_item_effects


class BaseItem(BaseEntity):
    """Base class for all collectible items."""

    __registry_category__ = "pickup"
    __registry_name__ = "default"

    def __init_subclass__(cls, **kwargs):
        """Auto-register item subclasses when they're defined."""
        super().__init_subclass__(**kwargs)
        EntityRegistry.auto_register(cls)

    def __init__(self, x, y, item_data=None, image=None, shape_data=None,
                 draw_manager=None, speed=50, despawn_y=None):
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
        self.layer = Layers.PICKUPS  # Same layer as enemies for now

        # Hitbox scale (smaller than visual for easier collection)
        self._hitbox_scale = 0.8

        # Movement
        self.velocity = pygame.Vector2(0, self.speed)

        # Store item data
        self.item_data = item_data or {}

        # Extract movement config from item_data
        self.movement_type = self.item_data.get("movement", "straight")
        self.speed = self.item_data.get("speed", speed)

        # If no image provided, build from item_data
        if image is None and shape_data is None:
            shape_data = {
                "type": "circle",
                "color": tuple(self.item_data.get("color", [0, 255, 100])),
                "size": tuple(self.item_data.get("size", [24, 24])),
                "kwargs": {}
            }
            # Rebuild the sprite using shape_data
            if draw_manager:
                self.image = draw_manager.prebake_shape(
                    shape_data["type"],
                    shape_data["size"],
                    shape_data["color"]
                )
                self.rect = self.image.get_rect(center=(x, y))
                self.shape_data = shape_data

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
            EVENTS.dispatch(ItemCollectedEvent(effects=self.get_effects()))

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

EntityRegistry.register("pickup", "default", BaseItem)
