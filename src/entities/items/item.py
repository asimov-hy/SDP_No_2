"""
item.py
-------
Defines the Item entity which represents a collectible object in the game world.
"""
import pygame
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import EntityCategory, LifecycleState
from src.core.runtime.game_settings import Layers, Display
from src.entities.items.item_types import ItemType
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
        Initializes a new item entity.

        Args:
            item_id (ItemType): The enum identifier for the item's type.
            position (tuple[int, int]): The (x, y) coordinate to spawn the item at.
            item_data (dict): A dictionary containing the item's properties from JSON.
            image (pygame.Surface): The pre-loaded sprite for this item.
        """
        super().__init__(x=x, y=y, image=image)

        # Item-specific data
        # self.item_id = item_id
        self.name = item_data.get("name", "Unknown Item")
        self.conditions = item_data.get("conditions", [])
        self.effects = item_data.get("effects", [])

        # Entity system properties
        self.category = EntityCategory.ITEM
        self.layer = Layers.BULLETS
        self.collision_tag = "item"

        # Movement properties
        self.velocity = pygame.Vector2(0, 75)  # Move downwards at a constant speed

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

        # If collected by the player, mark for removal
        if other.category == EntityCategory.PLAYER:
            self.mark_dead()

    def __repr__(self):
        return f"<Item(id={self.item_id.value}, pos={self.pos}, state={self.death_state})>"
