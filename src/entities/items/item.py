"""
item.py
-------
Defines the Item entity which represents a collectible object in the game world.
"""
import pygame

from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import EntityCategory, LifecycleState, CollisionTags
from src.core.runtime.game_settings import Layers, Display
from src.graphics.draw_manager import DrawManager


class Item(BaseEntity):
    """
    Represents a collectible item that moves down the screen.
    It inherits from BaseEntity to become a fully interactive game entity.
    """
    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x: float, y: float, item_data: dict, image: pygame.Surface, draw_manager: DrawManager):
        """
        Initialize a new item entity.

        Args:
            x (float): The x-coordinate to spawn the item at.
            y (float): The y-coordinate to spawn the item at.
            item_data (dict): A dictionary containing the item's properties from JSON.
            image (pygame.Surface): The pre-loaded sprite for this item.
            draw_manager (DrawManager): The manager responsible for rendering.
        """
        super().__init__(x=x, y=y, image=image, draw_manager=draw_manager)

        # Item-specific data
        self.name = item_data.get("name", "Unknown Item")
        self.effects = item_data.get("effects", [])

        # Entity system properties
        self.category = EntityCategory.ITEM
        self.layer = Layers.ENEMIES
        self.collision_tag = CollisionTags.PICKUP

        # Movement properties
        self.velocity = pygame.Vector2(0, 75)  # Move downwards at a constant speed

        # hitbox scale
        self._hitbox_scale = 0.9

    # ===========================================================
    # Core Update Loop
    # ===========================================================
    def update(self, dt: float):
        """
        Updates the item's position and checks screen boundaries.

        Args:
            dt (float): Time elapsed since the last frame.
        """
        if self.death_state != LifecycleState.ALIVE:
            return

        # Move the item downwards
        self.pos += self.velocity * dt
        self.sync_rect()

        # Mark as dead if it goes off the bottom of the screen
        if self.rect.top > Display.HEIGHT:
            self.mark_dead(immediate=True)

    # ===========================================================
    # Collision Interface
    # ===========================================================
    def on_collision(self, other: BaseEntity):
        """
        Handles collision with other entities.

        When an item collides with the player, it marks itself as dead
        to be removed from the game. The ItemManager is responsible for
        applying the item's effects to the player.

        Args:
            other (BaseEntity): The entity this item collided with.
        """
        if self.death_state != LifecycleState.ALIVE:
            return

        tag = getattr(other, "collision_tag", "unknown")
        # If collected by the player, mark for removal
        if tag == "player":
            from src.core.runtime.game_state import STATE
            STATE.item_effect_queue.append(self.effects)
            self.mark_dead(immediate=True)
        else:
            DebugLogger.trace(f"[CollisionIgnored] {type(self).__name__} vs {tag}")

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"name='{self.name}', "
            f"pos=({self.pos.x:.1f}, {self.pos.y:.1f}), "
            f"state='{self.death_state.name}'"
            ")"
        )
