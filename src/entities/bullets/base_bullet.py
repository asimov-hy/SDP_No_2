"""
base_bullet.py
--------------
Defines the base Bullet class providing shared logic for all bullet types.

Responsibilities
----------------
- Define position, velocity, and lifetime handling.
- Provide update and draw methods for derived bullet classes.
- Handle off-screen cleanup and base rendering logic.
- Manage base collision and damage delegation (on_hit).
"""

import pygame
from src.core import game_settings
from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.systems.combat.collision_hitbox import CollisionHitbox


class BaseBullet(BaseEntity):
    """Base class for all bullet entities."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, pos, vel, image=None, color=(255, 255, 255),
                 radius=3, owner="player", damage=1, hitbox_scale=0.9):
        """
        Initialize the base bullet.

        Args:
            pos (tuple[float, float]): Starting position.
            vel (tuple[float, float]): Velocity vector.
            image (pygame.Surface): Optional image for rendering.
            color (tuple[int, int, int]): RGB color for fallback rendering.
            radius (int): Hitbox radius when no image is used.
            owner (str): Entity type that fired the bullet ('player' or 'enemy').
            damage (int): Base damage value inflicted on collision.
        """
        # -------------------------------------------------------
        # 1) Initialize via BaseEntity (handles image/shape setup)
        # -------------------------------------------------------
        render_mode = "image" if image is not None else "shape"
        shape_type = "circle" if image is None else None
        radius = max(1, radius)
        size = (radius * 2, radius * 2)

        super().__init__(
            x=pos[0],
            y=pos[1],
            image=image,
            render_mode=render_mode,
            shape_type=shape_type,
            color=color,
            size=size
        )

        # -------------------------------------------------------
        # 2) Core Attributes
        # -------------------------------------------------------
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.alive = True
        self.owner = owner
        self.radius = radius
        self.damage = damage

        # -------------------------------------------------------
        # 3) Collision / Hitbox
        # -------------------------------------------------------
        self.collision_tag = f"{owner}_bullet"
        self.hitbox = CollisionHitbox(self, scale=hitbox_scale)
        self.has_hitbox = True

        # -------------------------------------------------------
        # 4) Layer Assignment
        # -------------------------------------------------------
        self.layer = game_settings.Layers.BULLETS

        # DebugLogger.trace(f"{self.collision_tag} created at {pos} → Vel={vel}")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt):
        """
        Update bullet position and check screen bounds.

        Responsibilities:
            - Move bullet according to velocity and delta time.
            - Deactivate when moving outside screen area.
        """
        if not self.alive:
            return

        self.pos += self.vel * dt
        self.rect.center = self.pos

        # Keep hitbox synced
        if self.has_hitbox:
            self.hitbox.update()

        # Off-screen cleanup (buffer for smooth exit)
        display_w, display_h = game_settings.Display.WIDTH, game_settings.Display.HEIGHT
        # Inside update()
        if (
                self.pos.y < -50 or self.pos.y > display_h + 50 or
                self.pos.x < -50 or self.pos.x > display_w + 50
        ):
            self.alive = False
            if getattr(DebugLogger, "ENABLED", True):
                DebugLogger.state(
                    f"{self.collision_tag} removed off-screen at {self.pos}",
                    category="entity_cleanup"
                )

    # ===========================================================
    # Collision Handling
    # ===========================================================
    def on_collision(self, target):
        """
        Entry point for collision events from CollisionManager.

        Delegates to handle_collision(), which can be overridden by
        derived bullet classes to implement custom behaviors.

        Args:
            target: The entity that this bullet collided with.
        """
        if not self.alive or target is self:
            return
        self.handle_collision(target)

    def handle_collision(self, target):
        """
        Default bullet behavior upon collision.

        Responsibilities:
            - Mark the bullet as inactive (destroyed).
            - Optionally log the collision event.

        This method can be overridden by subclasses to define
        specialized collision behavior (e.g., piercing, explosive,
        bouncing, or delayed destruction).

        Args:
            target: The entity that this bullet collided with.
        """
        self.alive = False
        if getattr(DebugLogger, "ENABLED", True):
            DebugLogger.state(
                f"{type(self).__name__} collided with {type(target).__name__} → destroyed",
                category="collision"
            )

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render the bullet to the given surface.

        Responsibilities:
            - Draw image if available.
            - Otherwise, render a simple circle.
        """
        super().draw(draw_manager)

        # Optional hitbox debug overlay
        if game_settings.Debug.HITBOX_VISIBLE and self.has_hitbox:
            self.hitbox.draw_debug(draw_manager.surface)
