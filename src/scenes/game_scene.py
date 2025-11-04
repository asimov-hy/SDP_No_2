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
from src.core.settings import Display, Layers
from src.core import settings

from src.entities.player import Player

from src.ui.ui_manager import UIManager
from src.ui.subsystems.hud_manager import HUDManager

from src.systems.spawn_manager import SpawnManager
from src.systems.stage_manager import StageManager



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
        self.draw_manager.load_image("player", "assets/images/player.png", scale=1.0)
        player_img = self.draw_manager.get_image("player")

        # Spawn player at bottom-center of screen
        start_x = (Display.WIDTH / 2) - (player_img.get_width() / 2)
        start_y = Display.HEIGHT - player_img.get_height() - 10

        self.player = Player(start_x, start_y, player_img)

        DebugLogger.init(f"Player entity initialized at ({start_x}, {start_y})")

        self.draw_manager.load_image("enemy_basic", "assets/images/enemies/enemy_basic.png", scale=1.0)
        DebugLogger.init("EnemyBasic image loaded successfully")

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
            {"spawn_time": 0.0, "enemy_type": "basic", "count": 3, "pattern": "line"},
            {"spawn_time": 4.0, "enemy_type": "basic", "count": 5, "pattern": "v"},
            {"spawn_time": 9.0, "enemy_type": "basic", "count": 8, "pattern": "line"},
        ]

        self.stage_manager = StageManager(self.spawner, STAGE_1_WAVES)
        DebugLogger.init("StageManager initialized with Stage 1 waves")

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
        move = self.input.get_normalized_move()

        # Player movement
        self.player.move_vec = move
        self.player.update(dt)

        # Wave-based enemy spawning
        self.stage_manager.update(dt)
        self.spawner.update(dt)

        # UI updates (HUD, menus)
        self.ui.update(pygame.mouse.get_pos())

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render all entities and UI elements to the draw queue.

        Args:
            draw_manager: DrawManager responsible for batching and rendering.
        """
        # Player rendering
        draw_manager.draw_entity(self.player, layer=Layers.PLAYER)

        # Wave-based enemies
        self.spawner.draw()

        # UI overlays
        self.ui.draw(draw_manager)