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
import math
import os

from src.core.debug.debug_logger import DebugLogger

from src.core.services.event_manager import get_events, BulletClearEvent

from src.entities.bullets.bullet_straight import StraightBullet
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
        self._bullet_configs = {}  # {owner: config_dict}
        self._bullet_images = {}  # {owner: pygame.Surface} - cached

        # Subscribe to bullet clear events
        get_events().subscribe(BulletClearEvent, self._on_bullet_clear)

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
            b._base_image = image  # CRITICAL: Update rotation source
            b.rect = b.image.get_rect(center=pos)
            b.shape_data = None  # Clear shape data when using image
            b._rotation_enabled = True  # Enable rotation for image bullets

            # Clear rotation cache to force regeneration
            if hasattr(b, '_rotation_cache'):
                b._rotation_cache.clear()
                b._cached_rotation_index = -1
        else:
            # Keep existing prebaked image, just update position
            b.rect.center = pos
            b._rotation_enabled = False

        # Only set radius for shape-based bullets (image bullets don't use these)
        if image is None:
            b.radius = radius

        b.owner = owner
        b.damage = damage
        b.death_state = LifecycleState.ALIVE
        b.collision_tag = f"{owner}_bullet"

    # ===========================================================
    # Pool Prewarming
    # ===========================================================
    def prewarm_pool(self, owner="player", count=50, bullet_class=StraightBullet,
                     image=None, color=None, radius=None, damage=None, hitbox_scale=0.9):
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
        config = self._bullet_configs.get(owner, {})

        if image is None:
            image = self._get_bullet_image(owner)
        if color is None:
            color = tuple(config.get("color", (255, 255, 255)))
        if radius is None:
            radius = config.get("radius", 3)
        if damage is None:
            damage = config.get("damage", 1)

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
    def spawn(self, pos, vel, image=None, color=None,
              radius=None, owner="player", damage=None, hitbox_scale=0.9):
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
        # Get defaults from config if not explicitly provided
        config = self._bullet_configs.get(owner, {})

        if image is None:
            image = self._get_bullet_image(owner)
        if color is None:
            color = tuple(config.get("color", (255, 255, 255)))
        if radius is None:
            radius = config.get("radius", 3)
        if damage is None:
            damage = config.get("damage", 1)

        bullet = self._get_bullet(pos, vel, image, color, radius, owner, damage, hitbox_scale)
        self.active.append(bullet)

        # DebugLogger.trace(f"[BulletSpawn] {bullet.collision_tag} at {pos} → Vel={vel}")

    def spawn_custom(self, bullet_class, pos, vel, image=None, color=None,
                     radius=None, owner="enemy", damage=None, hitbox_scale=0.9):
        """
        Create or reuse a bullet of a specified class (e.g., ZigzagBullet, SpiralBullet).
        Falls back to StraightBullet on failure.
        """
        config = self._bullet_configs.get(owner, {})

        if image is None:
            image = self._get_bullet_image(owner)
        if color is None:
            color = tuple(config.get("color", (255, 255, 255)))
        if radius is None:
            radius = config.get("radius", 3)
        if damage is None:
            damage = config.get("damage", 1)

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

    def _on_bullet_clear(self, event: BulletClearEvent):
        """Clear bullets matching owner within radius of center."""
        cleared = 0
        for bullet in self.active:
            if bullet.owner != event.owner:
                continue

            dist = math.hypot(
                bullet.pos.x - event.center[0],
                bullet.pos.y - event.center[1]
            )

            if dist <= event.radius:
                bullet.death_state = LifecycleState.DEAD
                cleared += 1

        if cleared > 0:
            DebugLogger.action(
                f"Cleared {cleared} {event.owner} bullets",
                category="combat"
            )

    # ===========================================================
    # Bullet Configuration
    # ===========================================================
    def register_bullet_config(self, owner: str, config: dict):
        """
        Register bullet configuration for an owner type.

        Args:
            owner: "player" or "enemy"
            config: Dict with 'path', 'size', 'color', 'radius', 'damage'
        """
        self._bullet_configs[owner] = config
        DebugLogger.init_sub(f"Registered bullet config for [{owner}]")

    def _get_bullet_image(self, owner: str):
        """
        Get cached bullet image for owner, loading if necessary.

        Args:
            owner: "player" or "enemy"

        Returns:
            pygame.Surface or None
        """
        # Return cached
        if owner in self._bullet_images:
            return self._bullet_images[owner]

        # Load from config
        config = self._bullet_configs.get(owner)
        if not config:
            return None

        path = config.get("path")
        size = tuple(config.get("size", [16, 32]))

        _NULL_IMAGE_PATH = "assets/images/null.png"

        # Try loading specified path
        if path and os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, size)
                self._bullet_images[owner] = img
                return img
            except pygame.error as e:
                DebugLogger.warn(f"Failed to load bullet image '{path}': {e}", category="loading")

        # Fallback to null.png
        if os.path.exists(_NULL_IMAGE_PATH):
            try:
                img = pygame.image.load(_NULL_IMAGE_PATH).convert_alpha()
                img = pygame.transform.scale(img, size)
                self._bullet_images[owner] = img
                return img
            except pygame.error:
                pass

        DebugLogger.warn(f"No bullet image for [{owner}], using shape", category="loading")
        return None
