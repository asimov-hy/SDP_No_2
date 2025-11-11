"""
bullet_manager.py
-----------------
System responsible for managing all bullet entities during gameplay.

Responsibilities
----------------
- Spawn and recycle bullet objects (object pooling for performance).
- Update bullet positions and states each frame.
- Queue bullet rendering through the DrawManager.
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
    def __init__(self, collision_manager=None):
        self.collision_manager = collision_manager
        self.active = []  # Active bullets currently in flight
        self.pool = []    # Inactive bullets available for reuse

        self.prewarm_pool(owner="player", count=50)

        DebugLogger.init(
            "║{:<59}║".format(f"\t[BulletManager][INIT]\t→ Pool ready"),
            show_meta=False
        )

    # ===========================================================
    # Bullet Creation / Reuse
    # ===========================================================
    def _get_bullet(self, pos, vel, image, color, radius, owner, damage, hitbox_scale):
        """Return a recycled or newly created StraightBullet."""
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

        # Recreate or sync rect
        if b.image:
            b.rect = b.image.get_rect(center=pos)
        else:
            b.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
            b.rect.center = pos

    # ===========================================================
    # Pool Prewarming
    # ===========================================================
    def prewarm_pool(self, owner="player", count=50, bullet_class=StraightBullet,
                     image=None, color=(255, 255, 255), radius=3, damage=1, hitbox_scale=0.9):
        """
        Pre-generate a number of inactive bullets and store them in the pool.
        This reduces runtime allocation spikes during gameplay.

        Args:
            owner (str): Bullet origin ('player' or 'enemy').
            count (int): Number of bullets to preallocate.
            bullet_class (type): Bullet class to instantiate.
            image (pygame.Surface): Optional bullet sprite.
            color (tuple[int, int, int]): Fallback color.
            radius (int): Bullet radius.
            damage (int): Damage per bullet.
            hitbox_scale (float): Hitbox size scale.
        """
        for _ in range(count):
            bullet = bullet_class(
                (0, 0), (0, 0),
                image=image, color=color,
                radius=radius, owner=owner,
                damage=damage, hitbox_scale=hitbox_scale
            )
            bullet.alive = False
            bullet.collision_tag = f"{owner}_bullet"
            self.pool.append(bullet)

        DebugLogger.state(f"Prewarmed {count} bullets for [{owner}] pool", category="combat")

    # ===========================================================
    # Spawning
    # ===========================================================
    def spawn(self, pos, vel, image=None, color=(255,255,255),
              radius=3, owner="player", damage=1, hitbox_scale=0.9):
        """
        Create or reuse a StraightBullet instance (default bullet type).

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
        bullet = self._get_bullet(pos, vel, image, color, radius, owner, damage, hitbox_scale)
        self.active.append(bullet)

        # Register hitbox with CollisionManager
        if self.collision_manager:
            self.collision_manager.register_hitbox(bullet)

        # DebugLogger.trace(f"[BulletSpawn] {bullet.collision_tag} at {pos} → Vel={vel}")

    def spawn_custom(self, bullet_class, pos, vel, image=None, color=(255, 255, 255),
                     radius=3, owner="enemy", damage=1, hitbox_scale=0.9):
        """
        Create or reuse a bullet of a specified class (e.g., ZigzagBullet, SpiralBullet).
        Falls back to StraightBullet on failure.
        """
        try:
            bullet = bullet_class(
                pos, vel,
                image=image, color=color,
                radius=radius, owner=owner,
                damage=damage, hitbox_scale=hitbox_scale,
            )
        except Exception as e:
            DebugLogger.warn(
                f"[BulletManager] Failed to spawn {bullet_class.__name__}: {e} → Using StraightBullet",
                category="combat"
            )
            bullet = StraightBullet(
                pos, vel,
                image=image, color=color,
                radius=radius, owner=owner,
                damage=damage, hitbox_scale=hitbox_scale,
            )

        bullet.collision_tag = f"{owner}_bullet"
        self.active.append(bullet)
        return bullet

    # ===========================================================
    # Update Cycle
    # ===========================================================
    def update(self, dt: float):
        """
        Update all active bullets and recycle any that are inactive.

        Args:
            dt (float): Delta time since last frame (seconds).
        """
        next_active = []

        for bullet in self.active:
            try:
                bullet.update(dt)
            except Exception as e:
                DebugLogger.warn(
                    f"[BulletUpdateError] {type(bullet).__name__}: {e}",
                    category="combat"
                )
                bullet.alive = False
                self.pool.append(bullet)
                continue

            # Lifecycle
            if bullet.alive and not self._is_offscreen(bullet):
                next_active.append(bullet)
            else:
                bullet.alive = False
                self.pool.append(bullet)

        self.active = next_active

    # ===========================================================
    # Offscreen Check Helper
    # ===========================================================
    def _is_offscreen(self, bullet) -> bool:
        """Return True if the bullet has moved beyond the visible area."""
        surface = pygame.display.get_surface()
        if not surface:
            return False
        return not surface.get_rect().colliderect(bullet.rect)

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
