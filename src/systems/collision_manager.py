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
from src.core.settings import Debug
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
        DebugLogger.trace("=== Collision Pass: Player ↔ Enemies ===")

        for enemy in self.spawn_manager.enemies:
            if not (enemy.alive and self.player.alive):
                continue
            if getattr(self.player, "hitbox", None) and getattr(enemy, "hitbox", None):
                if self.player.hitbox.rect.colliderect(enemy.hitbox.rect):
                    DebugLogger.trace(f"[Collision] Player <-> Enemy ({type(enemy).__name__})")
                    enemy.on_collision(self.player)
                    self.player.on_collision(enemy)

        # -------------------------------------------------------
        # 2. Bullets ↔ Entities (PlayerBullets → Enemies, EnemyBullets → Player)
        # -------------------------------------------------------
        DebugLogger.trace("=== Collision Pass: Bullets ↔ Entities ===")

        for bullet in list(self.bullet_manager.active):
            if not bullet.alive:
                continue

            # Player bullets hit enemies
            if bullet.owner == "player":
                for enemy in self.spawn_manager.enemies:
                    bullet_rect = bullet.hitbox.rect if hasattr(bullet, "hitbox") else bullet.rect
                    if enemy.alive and bullet_rect.colliderect(enemy.hitbox.rect):
                        DebugLogger.trace(f"[Collision] PlayerBullet -> {type(enemy).__name__}")
                        bullet.on_hit(enemy)
                        break

            # Enemy bullets hit player
            elif bullet.owner == "enemy":
                bullet_rect = bullet.hitbox.rect if hasattr(bullet, "hitbox") else bullet.rect
                if self.player.alive and getattr(self.player, "hitbox", None):
                    if bullet_rect.colliderect(self.player.hitbox.rect):
                        DebugLogger.trace(f"[Collision] EnemyBullet -> Player")
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
