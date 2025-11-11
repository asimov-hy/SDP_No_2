"""
game_scene.py
-------------
Defines the main in-game scene — includes core gameplay entities
and the player HUD overlay.

Responsibilities
----------------
- Initialize gameplay entities (e.g., Player).
- Update all active game logic each frame.
- Manage the in-game UI system (HUDManager, overlays).
- Forward input and events to appropriate subsystems.
"""

import pygame

from src.core.utils.debug_logger import DebugLogger
from src.core.game_settings import Debug

from src.entities.player import Player

from src.ui.ui_manager import UIManager
from src.ui.subsystems.hud_manager import HUDManager

from src.systems.world.spawn_manager import SpawnManager
from src.systems.world.level_manager import LevelManager
from src.systems.combat.bullet_manager import BulletManager
from src.systems.combat.collision_manager import CollisionManager


class GameScene:
    """Handles all gameplay entities, logic, and UI systems."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, scene_manager):
        """
        Initialize the game scene, UI, and entities.

        Args:
            scene_manager: Reference to SceneManager for access to display,
                           input, and draw subsystems.
        """
        DebugLogger.init("─" * 50, meta_mode="none")
        DebugLogger.init("Initializing GameScene", meta_mode="no_time")

        self.scene_manager = scene_manager
        self.display = scene_manager.display
        self.input = scene_manager.input
        self.draw_manager = scene_manager.draw_manager

        # UI System Setup
        self.ui = UIManager(self.display, self.draw_manager)

        # Base HUD (game overlay)
        try:
            self.ui.attach_subsystem("hud", HUDManager())
        except Exception as e:
            DebugLogger.warn(f"HUDManager unavailable: {e}")

        # Entity Setup

        # spawn player
        self.player = Player(draw_manager=self.draw_manager, input_manager=self.input)

        # Bullet Manager Setup
        self.bullet_manager = BulletManager()

        self.player.bullet_manager = self.bullet_manager
        DebugLogger.init("Linked [BulletManager] to [Player]", sub=2, meta_mode="none", is_last=True)

        # Collision Manager Setup
        self.collision_manager = CollisionManager(
            self.player,
            self.bullet_manager,
            None
        )

        self.bullet_manager.collision_manager = self.collision_manager
        DebugLogger.init("Linked [CollisionManager] to [BulletManager]", sub=2, meta_mode="none", is_last=True)

        # Register player's hitbox through the CollisionManager
        self.player.hitbox = self.collision_manager.register_hitbox(
            self.player,
            scale=self.player.hitbox_scale
        )
        DebugLogger.init("Linked [Player] to [CollisionHitbox]", meta_mode="none", sub=2, is_last=True)

        # ===========================================================
        # Spawn Manager Setup
        # ===========================================================
        self.spawn_manager = SpawnManager(self.draw_manager, self.display, self.collision_manager)

        self.collision_manager.spawn_manager = self.spawn_manager

        self.spawn_manager.enable_pooling("enemy", "straight", prewarm_count=10)

        # ===========================================================
        # Stage Manager Setup (Predefined Waves)
        # ===========================================================
        # Example stage definition — can be replaced with data or JSON later
        STAGE_1_WAVES = [
            {"spawn_time": 0.0, "enemy_type": "straight", "count": 3, "pattern": "line"},
            {"spawn_time": 4.0, "enemy_type": "straight", "count": 5, "pattern": "v"},
            {"spawn_time": 9.0, "enemy_type": "straight", "count": 8, "pattern": "line"},
        ]

        self.level_manager = LevelManager(self.spawn_manager, STAGE_1_WAVES)
        DebugLogger.init("LevelManager loaded: Stage 1 waves", sub=2, meta_mode="none", is_last=True)

        DebugLogger.init("─" * 50, meta_mode="none")

    # ===========================================================
    # Event Handling
    # ===========================================================
    def handle_event(self, event):
        """
        Forward input and system events to UI and entities.

        Args:
            event (pygame.event.Event): The event to process.
        """
        self.ui.handle_event(event)

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Update gameplay logic and UI each frame.

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """

        # 1) Player Input & Update
        move = self.input.get_normalized_move()
        self.player.move_vec = move
        self.player.update(dt)

        # 2) Enemy Spawn & Stage Progression
        self.level_manager.update(dt)
        self.spawn_manager.update(dt)

        # 3) Collision Phase
        self.collision_manager.update()
        self.collision_manager.detect()
        self.spawn_manager.cleanup()

        # 5) Bullet Update (after collision)
        # Update positions for remaining bullets that survived collisions.
        self.bullet_manager.update(dt)

        # 6) UI Update
        # Update HUD and overlays last, so they reflect the most recent state
        # (e.g., score, health after collisions).
        self.ui.update(pygame.mouse.get_pos())

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render all entities and UI elements to the draw queue.

        Args:
            draw_manager (DrawManager): Centralized renderer responsible for batching and displaying.
        """
        # Rendering Order (Layer Priority)
        self.spawn_manager.draw()
        self.bullet_manager.draw(draw_manager)
        self.player.draw(draw_manager)
        self.ui.draw(draw_manager)

        # Optional Debug Rendering
        if Debug.HITBOX_VISIBLE:
            self.collision_manager.draw_debug(draw_manager)

    # ===========================================================
    # Utilities
    # ===========================================================
    def get_pool_stats(self) -> dict:
        """Return current pool usage statistics."""
        stats = {}
        for key, pool in self.pools.items():
            category, type_name = key
            stats[f"{category}:{type_name}"] = {
                "available": len(pool),
                "enabled": self.pool_enabled.get(key, False)
            }
        return stats