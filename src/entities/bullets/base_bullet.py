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
from src.systems.combat.collision_hitbox import CollisionHitbox


class BaseBullet:
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
        # Core Properties
        # -------------------------------------------------------
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(vel)
        self.alive = True
        self.owner = owner
        self.image = image
        self.color = color
        self.radius = radius
        self.damage = damage

        # -------------------------------------------------------
        # Rect Setup
        # -------------------------------------------------------
        if self.image:
            self.rect = self.image.get_rect(center=pos)
        else:
            self.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            self.rect.center = pos

        # -------------------------------------------------------
        # Collision Tag & Hitbox
        # -------------------------------------------------------
        self.collision_tag = f"{owner}_bullet"
        self.hitbox = CollisionHitbox(self, scale=hitbox_scale)
        self.has_hitbox = True

        # DebugLogger.state(f"[BulletSpawn] {self.collision_tag} created at {pos} → Vel={vel}")

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
        if self.hitbox:
            self.hitbox.update()

        # Off-screen cleanup (buffer for smooth exit)
        if (
            self.pos.y < -50 or self.pos.y > game_settings.Display.HEIGHT + 50 or
            self.pos.x < -50 or self.pos.x > game_settings.Display.WIDTH + 50
        ):
            self.alive = False
            DebugLogger.state(
                f"{self.collision_tag} removed off-screen at {self.pos}",
                category="entity_cleanup"
            )

    # ===========================================================
    # Collision Logic
    # ===========================================================
    def on_hit(self, target):
        """
        Delegate damage application to the target entity.

        Args:
            target: Entity hit by this bullet (Player, Enemy, etc.)
        """
        if not self.alive:
            return  # Prevent multiple hits per frame
        if not getattr(target, "alive", True):
            return

        if not hasattr(target, "take_damage"):
            DebugLogger.warn(f"Target {type(target).__name__} has no take_damage()")
            return

        DebugLogger.state(
            f"{type(self).__name__} ({self.owner}) hit {type(target).__name__} "
            f"→ Damage={self.damage}"
        )

        self.alive = False
        target.take_damage(self.damage, source=type(self).__name__)

    def on_collision(self, target):
        """
        Compatibility handler for CollisionManager.

        Delegates to on_hit() to maintain backward compatibility
        with existing bullet logic.
        """
        if target is self:
            return
        self.on_hit(target)

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, surface):
        """
        Render the bullet to the given surface.

        Responsibilities:
            - Draw image if available.
            - Otherwise, render a simple circle.
        """
        if self.image:
            surface.blit(self.image, self.rect)
        else:
            pygame.draw.circle(surface, self.color, self.rect.center, self.radius)

        # Optional hitbox debug overlay
        if game_settings.Debug.HITBOX_VISIBLE:
            self.hitbox.draw_debug(surface)
