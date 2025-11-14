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
import random
from src.core.runtime.game_settings import Display, Layers
from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import CollisionTags, LifecycleState, EntityCategory
from src.entities.entity_registry import EntityRegistry
from src.graphics.animations.animation_effects.death_animation import death_fade


class BaseEnemy(BaseEntity):
    """Base class providing shared logic for all enemy entities_animation."""

    # Pre-computed direction vectors for auto-direction (optimization)
    _DIR_DOWN = (0, 1)
    _DIR_UP = (0, -1)
    _DIR_LEFT = (-1, 0)
    _DIR_RIGHT = (1, 0)
    _DIR_DOWN_LEFT = (-1, 1)
    _DIR_DOWN_RIGHT = (1, 1)
    _DIR_UP_LEFT = (-1, -1)
    _DIR_UP_RIGHT = (1, -1)

    def __init_subclass__(cls, **kwargs):
        """Auto-register enemy subclasses when they're defined."""
        super().__init_subclass__(**kwargs)
        EntityRegistry.auto_register(cls)

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image=None, shape_data=None, draw_manager=None,
                 speed=100, health=None, direction=None, spawn_edge=None, **kwargs):

        """
        Args:
            x, y: Position
            image: Pre-made sprite (image mode)
            shape_data: Shape definition (shape mode)
            draw_manager: Required for shape mode
            speed: Movement speed
            health: HP
        """
        super().__init__(x, y, image=image, shape_data=shape_data, draw_manager=draw_manager)
        self.speed = speed
        self.health = health if health is not None else 1
        self.max_health = self.health

        self._rotation_enabled = True

        # Collision setup
        self.collision_tag = CollisionTags.ENEMY
        self.category = EntityCategory.ENEMY
        self.layer = Layers.ENEMIES

        # hitbox scale
        self._hitbox_scale = 0.9

        if direction is None:
            self.velocity = self._auto_direction_from_edge(spawn_edge)
        else:
            self.velocity = pygame.Vector2(direction)

        # Normalize and apply speed
        if self.velocity.length_squared() > 0:
            self.velocity = self.velocity.normalize() * self.speed

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
        if self.is_offscreen():
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

    def _auto_direction_from_edge(self, edge):

        if edge is None:
            return pygame.Vector2(0, 1)

        edge = edge.lower()

        # Screen dimensions
        width = Display.WIDTH
        height = Display.HEIGHT

        # Get current normalized position (0 to 1)
        nx = self.pos.x / width
        ny = self.pos.y / height

        # Zone split percentages
        Z1 = 0.35  # left/top zone
        Z2 = 0.35  # right/bottom zone
        # center zone is implicit (1 - Z1 - Z2) = 0.30

        # ----------------------------------------------------
        # TOP EDGE
        # ----------------------------------------------------
        if edge == "top":
            if nx < Z1:
                # left 35 percent → inward or right-inward
                options = [self._DIR_DOWN, self._DIR_DOWN_RIGHT]
            elif nx > 1 - Z2:
                # right 35 percent → inward or left-inward
                options = [self._DIR_DOWN, self._DIR_DOWN_LEFT]
            else:
                # center 30 percent → all 3 inward dirs
                options = [self._DIR_DOWN, self._DIR_DOWN_LEFT, self._DIR_DOWN_RIGHT]

        # ----------------------------------------------------
        # BOTTOM EDGE
        # ----------------------------------------------------
        elif edge == "bottom":
            if nx < Z1:
                options = [self._DIR_UP, self._DIR_UP_RIGHT]
            elif nx > 1 - Z2:
                options = [self._DIR_UP, self._DIR_UP_LEFT]
            else:
                options = [self._DIR_UP, self._DIR_UP_LEFT, self._DIR_UP_RIGHT]

        # ----------------------------------------------------
        # LEFT EDGE
        # ----------------------------------------------------
        elif edge == "left":
            if ny < Z1:
                options = [self._DIR_DOWN_RIGHT, self._DIR_RIGHT]
            elif ny > 1 - Z2:
                options = [self._DIR_UP_RIGHT, self._DIR_RIGHT]
            else:
                options = [self._DIR_RIGHT, self._DIR_UP_RIGHT, self._DIR_DOWN_RIGHT]

        # ----------------------------------------------------
        # RIGHT EDGE
        # ----------------------------------------------------
        elif edge == "right":
            if ny < Z1:
                options = [self._DIR_DOWN_LEFT, self._DIR_LEFT]
            elif ny > 1 - Z2:
                options = [self._DIR_UP_LEFT, self._DIR_LEFT]
            else:
                options = [self._DIR_LEFT, self._DIR_UP_LEFT, self._DIR_DOWN_LEFT]

        else:
            return pygame.Vector2(0, 1)

        chosen = random.choice(options)
        return pygame.Vector2(chosen)

    def reset(self, x, y, direction=None, speed=None, health=None, spawn_edge=None, **kwargs):
        super().reset(x, y)

        if speed is not None:
            self.speed = speed
        if health is not None:
            self.health = health
            self.max_health = health

        if direction is None:
            self.velocity = self._auto_direction_from_edge(spawn_edge)
        else:
            self.velocity = pygame.Vector2(direction)

        if self.velocity.length_squared() > 0:
            self.velocity = self.velocity.normalize() * self.speed

        self.update_rotation()
