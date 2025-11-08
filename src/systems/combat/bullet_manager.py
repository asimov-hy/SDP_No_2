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

from src.entities.bullets.bullet_straight import StraightBullet
from src.core.game_settings import Layers
from src.core.utils.debug_logger import DebugLogger


class BulletManager:
    """Handles spawning, pooling, and rendering of all active bullets."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self):
        self.active = []  # currently active bullets
        self.pool = []    # inactive bullets ready for reuse
        self.bullets = self.active
        DebugLogger.init("║{:<59}║".format(f"\t[BulletManager][INIT]\t→ Pool ready"), show_meta=False)

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
        # Reuse from pool if possible
        if self.pool:
            b = self.pool.pop()
            b.pos.update(pos)
            b.vel.update(vel)
            b.alive = True
            b.owner = owner
            b.image = image
            b.color = color
            b.radius = radius
            b.damage = damage

            if b.image:
                b.rect = b.image.get_rect(center=pos)
            else:
                if b.image:
                    b.rect = b.image.get_rect(center=pos)
                else:
                    import pygame
                    b.rect = pygame.Rect(0, 0, radius * 2, radius * 2)
                    b.rect.center = pos

        else:
            b = StraightBullet(
                pos, vel, image=image, color=color,
                radius=radius, owner=owner, damage=damage,
                hitbox_scale=hitbox_scale
            )

        # Update or recreate hitbox
        if not hasattr(b, "hitbox"):
            from src.systems.combat.collision_hitbox import CollisionHitbox
            b.hitbox = CollisionHitbox(b, scale=hitbox_scale)
        else:
            b.hitbox.update()

        b.hitbox.rect.topleft = b.rect.topleft

        self.active.append(b)


    # ===========================================================
    # Update Cycle
    # ===========================================================
    def update(self, dt):
        """Update bullets positions and recycle any that are inactive."""
        alive_bullets = []
        for b in self.active:
            b.update(dt)

            if hasattr(b, "hitbox"):
                b.hitbox.rect.topleft = b.rect.topleft

            if b.alive:
                alive_bullets.append(b)
            else:
                self.pool.append(b)
        self.active = alive_bullets

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Queue all active bullets for rendering.

        Args:
            draw_manager (DrawManager): Global DrawManager instance.
        """
        import pygame
        from src.core.game_settings import Debug

        for b in self.active:
            if b.image:
                draw_manager.queue_draw(b.image, b.rect, layer=Layers.BULLETS)
            else:
                surf = pygame.Surface((b.radius * 2, b.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, b.color, (b.radius, b.radius), b.radius)
                draw_manager.queue_draw(surf, b.rect, layer=Layers.BULLETS)

            # Optional: render hitbox overlay
            if getattr(Debug, "ENABLE_HITBOX", False) and hasattr(b, "hitbox"):
                if hasattr(draw_manager, "surface") and getattr(Debug, "ENABLE_HITBOX", False):
                    b.hitbox.draw_debug(draw_manager.surface)
