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
- Forward input and events to appropriate components.
"""

import pygame

from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Debug

from src.entities.player import Player

from src.ui.ui_manager import UIManager
from src.ui.hud_manager import HUDManager

from src.systems.combat.bullet_manager import BulletManager
from src.systems.collision.collision_manager import CollisionManager

from src.systems.world.spawn_manager import SpawnManager
from src.systems.world.level_manager import LevelManager


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
                           input, and draw components.
        """
        DebugLogger.section("Initializing Scene: GameScene")

        self.scene_manager = scene_manager
        self.display = scene_manager.display
        self.input_manager = scene_manager.input_manager
        self.draw_manager = scene_manager.draw_manager

        # UI System Setup
        self.ui = UIManager(self.display, self.draw_manager)

        # Base HUD (game overlay)
        try:
            self.ui.attach_subsystem("hud", HUDManager())
        except Exception as e:
            DebugLogger.fail(f"HUDManager unavailable: {e}")

        # spawn player
        self.player = Player(draw_manager=self.draw_manager, input_manager=self.input_manager)

        # Bullet Manager Setup
        self.bullet_manager = BulletManager()

        self.player.bullet_manager = self.bullet_manager
        DebugLogger.init_sub("Connected [Player] → [BulletManager]")

        # Collision Manager Setup
        self.collision_manager = CollisionManager(
            self.player,
            self.bullet_manager,
            None
        )

        self.bullet_manager.collision_manager = self.collision_manager
        DebugLogger.init_sub("Bound [CollisionManager] to [BulletManager]")

        # Register player's hitbox through the CollisionManager
        self.player.hitbox = self.collision_manager.register_hitbox(
            self.player,
            scale=self.player.hitbox_scale
        )
        DebugLogger.init_sub("Registered [Player] with [CollisionManager]")

        # ===========================================================
        # Spawn Manager Setup
        # ===========================================================
        self.spawn_manager = SpawnManager(self.draw_manager, self.display, self.collision_manager)

        self.collision_manager.spawn_manager = self.spawn_manager

        self.spawn_manager.enable_pooling("enemy", "straight", prewarm_count=10)

        # ===========================================================
        # Level Manager Setup
        # ===========================================================
        self.level_manager = LevelManager(self.spawn_manager)

        DebugLogger.section("- Finished Initialization", only_title=True)
        DebugLogger.section("─" * 59 + "\n", only_title=True)

        self.paused = False

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

        if self.paused:
            return

        # 1) Player Input & Update
        move = self.input_manager.get_normalized_move()
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

    # ===========================================================
    # Lifecycle Hooks
    # ===========================================================
    def on_enter(self):
        DebugLogger.state("on_enter()")
        self.level_manager.load("src/data/Stage 1.json")

    def on_exit(self):
        DebugLogger.state("on_exit()")

    def on_pause(self):
        self.paused = True
        self.level_manager.stage_active = False
        DebugLogger.state("on_pause()")

    def on_resume(self):
        DebugLogger.state("on_resume()")

    def reset(self):
        DebugLogger.state("reset()")
