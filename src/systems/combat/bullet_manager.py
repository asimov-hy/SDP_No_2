"""
bullet_manager.py
-----------------
System responsible for managing all bullets entities during gameplay.

Responsibilities
----------------
- Spawn and recycle bullets objects (object pooling for performance).
- Update bullets positions and states each frame.
- Queue bullets rendering through the DrawManager.
- Maintain ownership (player/enemy) for collision and effects.
"""

import pygame
from src.entities.bullets.bullet_straight import StraightBullet
from src.core.game_settings import Debug
from src.core.utils.debug_logger import DebugLogger
from src.systems.combat.collision_hitbox import CollisionHitbox


class BulletManager:
    """Handles spawning, pooling, and rendering of all active bullets."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self):
        self.active = []  # Active bullets currently in flight
        self.pool = []    # Inactive bullets available for reuse

        DebugLogger.init("║{:<59}║".format(f"\t[BulletManager][INIT]\t→ Pool ready"), show_meta=False)

    # ===========================================================
    # Bullet Creation / Reuse
    # ===========================================================
    def _get_bullet(self, pos, vel, image, color, radius, owner, damage, hitbox_scale):
        """Return a recycled or newly created bullet."""
        if self.pool:
            bullet = self.pool.pop()
            self._reset_bullet(bullet, pos, vel, image, color, radius, owner, damage, hitbox_scale)
        else:
            bullet = StraightBullet(
                pos, vel,
                image=image, color=color,
                radius=radius, owner=owner,
                damage=damage, hitbox_scale=hitbox_scale,
            )

        bullet.collision_tag = f"{owner}_bullet"
        bullet.has_hitbox = True

        return bullet

    def _reset_bullet(self, b, pos, vel, image, color, radius, owner, damage, hitbox_scale):
        """Reset an existing bullet from the pool."""
        b.pos.update(pos)
        b.vel.update(vel)
        b.image = image
        b.color = color
        b.radius = radius
        b.owner = owner
        b.damage = damage
        b.alive = True
        b.collision_tag = f"{owner}_bullet"
        b.has_hitbox = True

        # Recreate or sync rect
        if b.image:
            b.rect = b.image.get_rect(center=pos)
        else:
            b.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            b.rect.center = pos

        # Ensure hitbox consistency
        if not getattr(b, "hitbox", None):
            b.hitbox = CollisionHitbox(b, scale=hitbox_scale)
        else:
            b.hitbox.update()

    # ===========================================================
    # Spawning
    # ===========================================================
    def spawn(self, pos, vel, image=None, color=(255, 255, 255),
              radius=3, owner="player", damage=1, hitbox_scale=0.9):
        """
        Create or reuse a bullet instance.

        Args:
            pos (tuple[float, float]): Starting position.
            vel (tuple[float, float]): Velocity vector.
            image (pygame.Surface): Optional bullet sprite.
            color (tuple[int, int, int]): Fallback color.
            radius (int): Circle radius when using default shape.
            owner (str): Bullet origin ('player' or 'enemy').
            damage (int): Damage dealt upon collision.
            hitbox_scale (float): Scale factor for bullet hitbox size.
        """
        b = self._get_bullet(pos, vel, image, color, radius, owner, damage, hitbox_scale)
        self.active.append(b)
        # DebugLogger.trace(f" {b.collision_tag} at {pos} → Vel={vel}")

    # ===========================================================
    # Update Cycle
    # ===========================================================
    def update(self, dt):
        """Update bullets positions and recycle any that are inactive."""
        i = 0
        for b in self.active:
            b.update(dt)

            if b.hitbox:
                b.hitbox.rect.center = b.rect.center

            if b.alive:
                self.active[i] = b
                i += 1
            else:
                self.pool.append(b)

        del self.active[i:]

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Queue all active bullets for rendering.

        Args:
            draw_manager (DrawManager): Global DrawManager instance.
        """
        for b in self.active:
            b.draw(draw_manager)

            # Debug: render hitbox overlay
            if Debug.HITBOX_VISIBLE and b.hitbox:
                draw_manager.queue_hitbox(b.hitbox.rect, b.hitbox._color_cache)

    # ===========================================================
    # Cleanup (External Call)
    # ===========================================================
    def cleanup(self):
        """Immediately remove or recycle inactive bullets."""
        before = len(self.active)
        self.active = [b for b in self.active if b.alive]
        removed = before - len(self.active)

        if removed > 0:
            DebugLogger.state(
                f"Cleaned up {removed} inactive bullets",
                category="entity_cleanup"
            )
