"""
enemy.py
--------
Defines the shared base class for all enemy entities.

Responsibilities
----------------
- Maintain core enemy properties (HP, speed, alive state).
- Handle common behaviors such as damage, destruction, and drawing.
- Provide a base interface for all enemy subclasses (basic, zigzag, etc.).
"""
from src.core.settings import Debug, Display, Layers
from src.entities.base_entity import BaseEntity
from src.core.utils.debug_logger import DebugLogger



class Enemy(BaseEntity):
    """Base class providing shared logic for all enemy entities."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image, speed=100, hp=1):
        """
        Initialize a base enemy entity.

        Args:
            x (float): Spawn X position.
            y (float): Spawn Y position.
            image (pygame.Surface): Enemy sprite image.
            speed (float, optional): Movement speed in pixels per second.
            hp (int, optional): Hit points before destruction.
        """
        super().__init__(x, y, image)
        self.speed = speed
        self.hp = hp
        self._trace_timer = 0.0

        if Debug.VERBOSE_ENTITY_INIT:
            DebugLogger.init(f"Enemy initialized at ({x}, {y})")

    # ===========================================================
    # Damage and State Handling
    # ===========================================================
    def take_damage(self, amount=1):
        """
        Apply damage to the enemy and mark it dead when HP reaches zero.

        Args:
            amount (int, optional): Amount of HP to subtract. Defaults to 1.
        """
        if not self.alive:
            DebugLogger.trace("Damage ignored (already destroyed)")
            return

        self.hp -= amount
        DebugLogger.state(f"HP reduced by {amount} → {self.hp}")

        if self.hp <= 0:
            self.alive = False
            DebugLogger.state(f"Destroyed at {self.rect.topleft}")

    # ===========================================================
    # Update Logic (To Be Overridden)
    # ===========================================================
    def update(self, dt: float):
        """
        Base update method — should be overridden by specific enemy types.

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """
        pass

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render the enemy sprite to the screen.

        Args:
            draw_manager: DrawManager instance responsible for batching render calls.
        """
        draw_manager.draw_entity(self, layer=Layers.ENEMIES)
        # if __debug__:  # or custom flag
        #     DebugLogger.trace(f"Drew enemy at {self.rect.topleft}")

