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
        self.scene_manager = scene_manager
        self.display = scene_manager.display
        self.input = scene_manager.input
        self.draw_manager = scene_manager.draw_manager

        DebugLogger.system("Initializing game scene")

        # ===========================================================
        # UI System Setup
        # ===========================================================
        self.ui = UIManager(self.display, self.draw_manager)

        # Base HUD (game overlay)
        try:
            self.ui.attach_subsystem("hud", HUDManager())
            DebugLogger.init("HUDManager attached successfully")
        except Exception as e:
            DebugLogger.warn(f"HUDManager unavailable: {e}")

        # ===========================================================
        # Entity Setup
        # ===========================================================

        # spawn player
        self.player = Player()

        self.draw_manager.load_image("enemy_straight", "assets/images/enemies/enemy_straight.png", scale=1.0)
        DebugLogger.init("EnemyStraight sprite loaded successfully")

        # ===========================================================
        # Spawn Manager Setup (Wave-Based Enemy Spawning)
        # ===========================================================
        self.spawner = SpawnManager(self.draw_manager, self.display)
        DebugLogger.init("SpawnManager initialized successfully")

        # ===========================================================
        # Stage Manager Setup (Predefined Waves)
        # ===========================================================
        # Example stage definition — can be replaced with data or JSON later
        STAGE_1_WAVES = [
            {"spawn_time": 0.0, "enemy_type": "straight", "count": 3, "pattern": "line"},
            {"spawn_time": 4.0, "enemy_type": "straight", "count": 5, "pattern": "v"},
            {"spawn_time": 9.0, "enemy_type": "straight", "count": 8, "pattern": "line"},
        ]

        self.stage_manager = LevelManager(self.spawner, STAGE_1_WAVES)
        DebugLogger.init("StageManager initialized with Stage 1 waves")

        # ===========================================================
        # Bullet Manager Setup
        # ===========================================================
        self.bullet_manager = BulletManager()
        self.player.bullet_manager = self.bullet_manager  # Give player access
        DebugLogger.init("BulletManager initialized and linked to Player")

        # ===========================================================
        # Collision Manager Setup
        # ===========================================================
        self.collision_manager = CollisionManager(
            self.player,
            self.bullet_manager,
            self.spawner
        )
        DebugLogger.init("CollisionManager initialized successfully")

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

        # ===========================================================
        # 1) Player Input & Update
        # ===========================================================
        move = self.input.get_normalized_move()
        self.player.move_vec = move
        self.player.update(dt)
        # Bullets are spawned here if player fires — so they exist this frame.

        # ===========================================================
        # 2) Enemy Spawn & Stage Progression
        # ===========================================================
        self.stage_manager.update(dt)
        self.spawner.update(dt)

        # ===========================================================
        # 3) Collision Phase
        # ===========================================================
        # Detect collisions *before* bullet update so bullets killed here
        # are removed immediately in the next step.
        try:
            self.collision_manager.detect()
        finally:
            # 4) Bullet & Enemy Cleanup
            # Cleanup ensures dead entities don’t persist visually.
            if hasattr(self.bullet_manager, "cleanup"):
                self.bullet_manager.cleanup()
            if hasattr(self.spawner, "cleanup"):
                self.spawner.cleanup()

        # ===========================================================
        # 5) Bullet Update (after collision)
        # ===========================================================
        # Update positions for remaining bullets that survived collisions.
        self.bullet_manager.update(dt)

        # ===========================================================
        # 6) UI Update
        # ===========================================================
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
        # =======================================================
        # Rendering Order (Layer Priority)
        # =======================================================
        self.spawner.draw()
        self.bullet_manager.draw(draw_manager)
        self.player.draw(draw_manager)
        self.ui.draw(draw_manager)

        # =======================================================
        # Optional Debug Rendering
        # =======================================================
        if Debug.HITBOX_VISIBLE:
            self.collision_manager.draw_debug(draw_manager)
