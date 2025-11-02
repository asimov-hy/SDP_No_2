"""
game_scene.py
-------------
Defines the in-game scene — includes gameplay entities and the main HUD.
"""

import pygame
from src.entities.player import Player
from src.ui.ui_manager import UIManager
from src.ui.subsystems.hud_manager import HUDManager

class GameScene:
    """Handles all gameplay entities, logic, and UI systems."""

    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.display = scene_manager.display
        self.input = scene_manager.input
        self.draw_manager = scene_manager.draw_manager

        # ----------------------------------------------------
        # UI Systems
        # ----------------------------------------------------
        self.ui = UIManager(self.display, self.draw_manager)


        # Base HUD (game overlay)
        try:
            self.ui.attach_subsystem("hud", HUDManager())
        except Exception as e:
            print(f"[WARN] HUDManager unavailable: {e}")

        # ----------------------------------------------------
        # Entities
        # ----------------------------------------------------
        self.draw_manager.load_image("player", "assets/images/player.png", scale=1.0)
        player_img = self.draw_manager.get_image("player")

        # Use scalable width/height from DisplayManager
        width, height = self.display.get_window_size()
        self.player = Player(width // 2, height - 80, player_img)

    # --------------------------------------------------------
    # Event Handling
    # --------------------------------------------------------

    def handle_event(self, event):
        """Handle input events (player + UI)."""


        # Pass all events to the UI
        self.ui.handle_event(event)

    # --------------------------------------------------------
    # Update Logic
    # --------------------------------------------------------

    def update(self, dt):
        """Update game entities and UI logic."""
        self.input.update()
        move = self.input.get_normalized_move()
        self.player.update(dt, move)
        self.ui.update(pygame.mouse.get_pos())

    # --------------------------------------------------------
    # Drawing
    # --------------------------------------------------------

    def draw(self, draw_manager):
        """Render entities and UI."""
        draw_manager.draw_entity(self.player, layer=1)
        self.ui.draw(draw_manager)
