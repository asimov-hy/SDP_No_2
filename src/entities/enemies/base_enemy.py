"""
base_enemy.py
--------------
Defines the shared base class for all enemy entities_animation.

Responsibilities
----------------
- Maintain core enemy properties (HP, speed, alive state).
- Handle common behaviors such as damage, destruction, and drawing.
- Provide a base interface for all enemy subclasses (straight, zigzag, shooter, etc.).
"""

import pygame
from src.core.runtime.game_settings import Display, Layers
from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import CollisionTags, LifecycleState, EntityCategory
from src.graphics.animations.animation_effects.death_animation import death_fade


class BaseEnemy(BaseEntity):
    """Base class providing shared logic for all enemy entities_animation."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image, speed=100, health=None):
        """
        Initialize a base enemy entity.

        Args:
            x (float): Spawn X position.
            y (float): Spawn Y position.
            image (pygame.Surface): Enemy sprite image.
            speed (float, optional): Movement speed (pixels per second).
            health (int, optional): HP before destruction. Defaults to HealthPresets.ENEMY_NORMAL.
        """
        super().__init__(x, y, image)
        self.speed = speed
        self.health = health if health is not None else 1
        self.max_health = self.health

        self._base_image = image
        self.rotation_angle = 0  # Degrees, 0 = pointing right

        # Collision setup
        self.collision_tag = CollisionTags.ENEMY
        self.category = EntityCategory.ENEMY
        self.layer = Layers.ENEMIES

        # hitbox scale
        self._hitbox_scale = 0.9

        # Default movement vector (downward)
        self.velocity = pygame.Vector2(0, 0)

    # ===========================================================
    # Damage and State Handling
    # ===========================================================
    def on_damage(self, amount: int):
        """
        Optional visual or behavioral response when the enemy takes damage.
        Override in subclasses for hit flash, particles, etc.
        """
        pass

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """Default downward movement for enemies."""
        if self.death_state == LifecycleState.DYING:
            if self.anim.update(self, dt):
                self.mark_dead(immediate=True)
            return

        if self.death_state != LifecycleState.ALIVE:
            return

        self.pos += self.velocity * dt
        self.sync_rect()
        self.update_rotation()

        # Mark dead if off-screen
        if self.rect.top > Display.HEIGHT:
            self.mark_dead(immediate=True)

    def take_damage(self, amount: int, source: str = "unknown"):
        """
        Reduce health by the given amount and handle death.
        Calls on_damage() and on_death() hooks as needed.
        """
        if self.death_state >= LifecycleState.DEAD:
            return

        self.health = max(0, self.health - amount)

        # Trigger optional reaction (e.g., flash, stagger)
        self.on_damage(amount)

        if self.health <= 0:
            self.mark_dead(immediate=False)
            self.on_death(source)

    def on_death(self, source):
        self.anim.play(death_fade, duration=0.5)

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """Render the enemy sprite to the screen."""
        draw_manager.draw_entity(self, layer=self.layer)

    def update_rotation(self):
        """
        Rotate image to match velocity direction.
        Only rotates if velocity changed (optimization).
        """
        if self._base_image is None or self.velocity.length_squared() == 0:
            return

        # Calculate angle from velocity (-90 because base triangle points up)
        target_angle = -self.velocity.as_polar()[1] - 90

        # Only rotate if angle changed (avoid unnecessary rotations)
        if abs(target_angle - self.rotation_angle) > 0.1:
            self.rotation_angle = target_angle
            self.image = pygame.transform.rotate(self._base_image, self.rotation_angle)
            # Update rect to match new rotated size
            old_center = self.rect.center
            self.rect = self.image.get_rect(center=old_center)

    # ===========================================================
    # Collision Handling
    # ===========================================================
    def on_collision(self, other):
        """Default collision response for enemies."""
        tag = getattr(other, "collision_tag", "unknown")

        if tag == "player_bullet":
            # DebugLogger.state(f"{type(self).__name__} hit by PlayerBullet")
            self.take_damage(1, source="player_bullet")

        elif tag == "player":
            self.take_damage(1, source="player_contact")

        else:
            DebugLogger.trace(f"[CollisionIgnored] {type(self).__name__} vs {tag}")
