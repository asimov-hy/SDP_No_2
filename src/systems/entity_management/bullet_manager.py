"""
bullet_manager.py
-----------------
System responsible for managing all bullet entities_animation during gameplay.

Responsibilities
----------------
- Spawn and recycle bullet objects (object pooling for performance).
- Update bullet positions and states each frame.
- Queue bullet rendering through the DrawManager.
- Maintain ownership (player/enemy) for collision and animation_effects.
"""

import pygame
from src.entities.bullets.bullet_straight import StraightBullet
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState


class BulletManager:
    """Handles spawning, pooling, and rendering of all active bullets."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, draw_manager=None, collision_manager=None):
        self.draw_manager = draw_manager
        self.collision_manager = collision_manager
        self.active = []  # Active bullets currently in flight
        self.pool = []   # Inactive bullets available for reuse

        # Only prewarm if draw_manager available
        if self.draw_manager:
            self.prewarm_pool(owner="player", count=50)

        DebugLogger.init_entry("BulletManager Initialized")

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
                draw_manager=self.draw_manager
            )

        bullet.collision_tag = f"{owner}_bullet"
        self._register_hitbox(bullet)
        return bullet

    def _reset_bullet(self, b, pos, vel, image, color, radius, owner, damage, hitbox_scale):
        """Reset an existing bullet from the pool."""
        b.pos.update(pos)
        b.vel.update(vel)

        # Only update image if explicitly provided (not None)
        if image is not None:
            b.image = image
            b.rect = b.image.get_rect(center=pos)
        else:
            # Keep existing prebaked image, just update position
            b.rect.center = pos

        b.color = color
        b.radius = radius
        b.owner = owner
        b.damage = damage
        b.death_state = LifecycleState.ALIVE
        b.collision_tag = f"{owner}_bullet"

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
                damage=damage, hitbox_scale=hitbox_scale,
                draw_manager=self.draw_manager
            )
            bullet.death_state = LifecycleState.DEAD
            bullet.collision_tag = f"{owner}_bullet"
            self.pool.append(bullet)

        DebugLogger.state(f"Prewarmed {count} bullets for [{owner}] pool", category="combat")

    def link_collision_manager(self, cm):
        self.collision_manager = cm
        DebugLogger.system("CollisionManager linked to BulletManager", category="combat")

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
                draw_manager=self.draw_manager
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
                draw_manager=self.draw_manager
            )

        bullet.collision_tag = f"{owner}_bullet"
        self.active.append(bullet)
        self._register_hitbox(bullet)
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
                bullet.death_state = LifecycleState.DEAD
                self._unregister_hitbox(bullet)
                self.pool.append(bullet)
                continue

            # Lifecycle
            if bullet.death_state < LifecycleState.DEAD and not self._is_offscreen(bullet):
                next_active.append(bullet)
            else:
                bullet.death_state = LifecycleState.DEAD
                self._unregister_hitbox(bullet)
                self.pool.append(bullet)

        self.active = next_active

    # ===========================================================
    # Offscreen Check Helper
    # ===========================================================
    def _is_offscreen(self, bullet) -> bool:
        """Return True if the bullet has moved beyond the visible area."""
        return bullet.is_offscreen()

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
    # Internal Helpers
    # ===========================================================
    def _register_hitbox(self, bullet):
        """Register bullet hitbox if collision manager is available."""
        if self.collision_manager:
            self.collision_manager.register_hitbox(bullet)

    def _unregister_hitbox(self, bullet):
        """Remove bullet from collision tracking."""
        if self.collision_manager:
            self.collision_manager.unregister_hitbox(bullet)
    # ===========================================================
    # Cleanup
    # ===========================================================
    def cleanup(self):
        """Immediately remove or recycle inactive bullets."""
        before = len(self.active)
        cleaned = []
        for b in self.active:
            if b.death_state < LifecycleState.DEAD:
                cleaned.append(b)
            else:
                self._unregister_hitbox(b)
                self.pool.append(b)

        self.active = cleaned
        removed = before - len(self.active)

        if removed > 0:
            DebugLogger.state(
                f"Cleaned up {removed} inactive bullets",
                category="entity_cleanup"
            )
