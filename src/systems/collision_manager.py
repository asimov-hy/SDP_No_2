"""
collision_manager.py
--------------------
Handles collision detection between player, enemies, and bullets.

Responsibilities
----------------
- Maintain modular per-entity hitboxes.
- Check collisions each frame.
- Trigger damage or destruction on collision.
- Provide optional debug visualization.
"""

import pygame
from src.core.settings import Debug
from src.core.utils.debug_logger import DebugLogger
from src.systems.hitbox import Hitbox

class CollisionManager:
    def __init__(self, player, bullet_manager, spawn_manager):
        self.player = player
        self.bullet_manager = bullet_manager
        self.spawn_manager = spawn_manager

        # Attach hitboxes
        self.player.hitbox = Hitbox(player, scale=getattr(player, "hitbox_scale", 1.0))
        for e in self.spawn_manager.enemies:
            e.hitbox = Hitbox(e, scale=getattr(e, "hitbox_scale", 1.0))

    # -----------------------------------------------------------
    # Per-frame update
    # -----------------------------------------------------------
    def update(self, surface=None):
        # Update hitboxes
        self.player.hitbox.update()
        for enemy in self.spawn_manager.enemies:
            enemy.hitbox.update()

        # =======================================================
        # Bullet collisions
        # =======================================================
        for bullet in list(self.bullet_manager.bullets):
            if not bullet.alive:
                continue

            b_rect = bullet.rect
            owner = bullet.owner

            if owner == "player":
                # Check vs enemies
                for enemy in self.spawn_manager.enemies:
                    if enemy.alive and b_rect.colliderect(enemy.hitbox.rect):
                        enemy.take_damage()
                        bullet.alive = False
                        break
            elif owner == "enemy":
                # Check vs player
                if not self.player.invincible and b_rect.colliderect(self.player.hitbox.rect):
                    self.player.health -= 1
                    bullet.alive = False
                    if self.player.health <= 0:
                        self.player.alive = False
                        DebugLogger.state("Player destroyed!")
            else:
                DebugLogger.warn(f"Bullet with unknown owner: {owner}")

        # =======================================================
        # Player ↔ Enemy collisions
        # =======================================================
        for enemy in self.spawn_manager.enemies:
            if enemy.alive and self.player.alive:
                if self.player.hitbox.rect.colliderect(enemy.hitbox.rect):
                    self.player.health -= 1
                    enemy.alive = False
                    if self.player.health <= 0:
                        self.player.alive = False
                    DebugLogger.state("Player collided with enemy!")

        # =======================================================
        # Optional debug drawing
        # =======================================================
        if Debug.ENABLE_HITBOX and surface:
            self.player.hitbox.draw_debug(surface)
            for enemy in self.spawn_manager.enemies:
                enemy.hitbox.draw_debug(surface)
