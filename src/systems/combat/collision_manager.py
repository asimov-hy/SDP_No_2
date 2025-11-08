"""
collision_manager.py
--------------------
Simplified modular collision handler.
Detects overlaps and delegates actual effects
to entities and bullets themselves.

Responsibilities
----------------
- Detect collisions between bullets ↔ entities.
- Delegate behavior to bullet.on_hit() or entity.on_collision().
- Provide optional hitbox debug visualization.
"""

import pygame
from src.core.game_settings import Debug
from src.core.utils.debug_logger import DebugLogger


class CollisionManager:
    """Detects collisions but lets objects decide what happens."""

    def __init__(self, player, bullet_manager, spawn_manager):
        self.player = player
        self.bullet_manager = bullet_manager
        self.spawn_manager = spawn_manager

    # ===========================================================
    # Per-frame update
    # ===========================================================
    def update(self, surface=None):
        """
        Perform collision detection only — no direct damage logic.
        """
        # -------------------------------------------------------
        # 1. Player ↔ Enemy
        # -------------------------------------------------------

        for enemy in self.spawn_manager.enemies:
            if not (enemy.alive and self.player.alive):
                continue
            if getattr(self.player, "hitbox", None) and getattr(enemy, "hitbox", None):
                # Sync hitbox positions before checking
                self.player.hitbox.rect.topleft = self.player.rect.topleft
                enemy.hitbox.rect.topleft = enemy.rect.topleft

                if self.player.hitbox.rect.colliderect(enemy.hitbox.rect):
                    DebugLogger.state(f"[Collision] Player <-> {type(enemy).__name__}")
                    enemy.on_collision(self.player)
                    self.player.on_collision(enemy)

        # -------------------------------------------------------
        # 2. Bullets ↔ Entities (PlayerBullets → Enemies, EnemyBullets → Player)
        # -------------------------------------------------------

        for bullet in list(self.bullet_manager.active):
            if not bullet.alive:
                continue

            # Player bullets hit enemies
            if bullet.owner == "player":
                for enemy in self.spawn_manager.enemies:
                    if not (enemy.alive and getattr(enemy, "hitbox", None)):
                        continue

                    # Sync hitbox positions before check
                    if hasattr(bullet, "hitbox"):
                        bullet.hitbox.rect.topleft = bullet.rect.topleft
                    enemy.hitbox.rect.topleft = enemy.rect.topleft

                    bullet_rect = bullet.hitbox.rect if hasattr(bullet, "hitbox") else bullet.rect
                    if bullet_rect.colliderect(enemy.hitbox.rect):
                        DebugLogger.state(f"[Collision] PlayerBullet -> {type(enemy).__name__}")
                        bullet.on_hit(enemy)
                        break

            # Enemy bullets hit player
            elif bullet.owner == "enemy":
                bullet_rect = bullet.hitbox.rect if hasattr(bullet, "hitbox") else bullet.rect
                if self.player.alive and getattr(self.player, "hitbox", None):
                    if bullet_rect.colliderect(self.player.hitbox.rect):
                        DebugLogger.state("[Collision] EnemyBullet -> Player")
                        bullet.on_hit(self.player)

        # -------------------------------------------------------
        # 3. Optional debug visualization
        # -------------------------------------------------------
        if Debug.ENABLE_HITBOX and surface:
            if getattr(self.player, "hitbox", None):
                self.player.hitbox.draw_debug(surface)
            for enemy in self.spawn_manager.enemies:
                if getattr(enemy, "hitbox", None):
                    enemy.hitbox.draw_debug(surface)

            for bullet in self.bullet_manager.active:
                if getattr(bullet, "hitbox", None):
                    bullet.hitbox.draw_debug(surface)
