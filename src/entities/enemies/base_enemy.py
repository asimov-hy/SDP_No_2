"""
base_enemy.py
--------------
Defines the shared base class for all enemy entities.

Responsibilities
----------------
- Maintain core enemy properties (HP, speed, alive state).
- Handle common behaviors such as damage, destruction, and drawing.
- Provide a base interface for all enemy subclasses (straight, zigzag, shooter, etc.).
"""

import pygame
from src.core.game_settings import Display, Debug, Layers
from src.entities.base_entity import BaseEntity
from src.core.utils.debug_logger import DebugLogger
from src.systems.combat.collision_hitbox import CollisionHitbox


class EnemyBaseEntity(BaseEntity):
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

        # -------------------------------------------------------
        # Collision setup
        # -------------------------------------------------------
        self.collision_tag = "enemy"
        self.has_hitbox = False

        self.hitbox = CollisionHitbox(self, scale=0.85)  # Default scale, customizable per subclass
        self.has_hitbox = True

        # -------------------------------------------------------
        # Movement & State
        # -------------------------------------------------------
        self.velocity = pygame.Vector2(0, self.speed)

    # ===========================================================
    # Damage and State Handling
    # ===========================================================
    def take_damage(self, amount=1, source="unknown"):
        """
        Apply damage to the enemy and mark it dead when HP reaches zero.

        Args:
            amount (int, optional): Amount of HP to subtract. Defaults to 1.
            source (str, optional): Damage source tag or entity name.
        """
        if not self.alive:
            DebugLogger.trace("Damage ignored (already destroyed)")
            return

        self.hp -= amount
        DebugLogger.state(
            f"[EnemyDamage] {type(self).__name__} took {amount} from {source} → HP={self.hp}"
        )

        if self.hp <= 0:
            self.alive = False
            DebugLogger.state(f"[Death] {type(self).__name__} destroyed at {self.rect.topleft}")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """Default downward movement for enemies."""
        if not self.alive:
            return

        self.pos.y += self.speed * dt
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

        if self.hitbox:
            self.hitbox.update()

        # Mark dead if off-screen
        if self.pos.y > Display.HEIGHT:
            self.alive = False

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """Render the enemy sprite to the screen."""
        draw_manager.draw_entity(self, layer=Layers.ENEMIES)

    # ===========================================================
    # Collision Handling
    # ===========================================================
    def on_collision(self, other):
        """Default collision response for enemies."""
        tag = getattr(other, "collision_tag", "unknown")

        if tag == "player_bullet":
            self.take_damage(1, source="player_bullet")
            DebugLogger.state(f"[Collision] {type(self).__name__} hit by PlayerBullet")

        elif tag == "player":
            self.take_damage(1, source="player_contact")
            DebugLogger.state(f"[Collision] {type(self).__name__} collided with Player")

        else:
            DebugLogger.trace(f"[CollisionIgnored] {type(self).__name__} vs {tag}")
