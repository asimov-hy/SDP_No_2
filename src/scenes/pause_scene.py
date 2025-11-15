"""
pause_scene.py
--------------
Displays an overlay when the game is paused.
Provides options to resume or quit to the main menu.

Responsibilities:
- Render "Paused" title and UI buttons.
- Handle button clicks to transition back to GameScene or MainMenuScene.
"""

import pygame
import sys

from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Display

from src.ui.components.ui_button import UIButton

FONT_PATH = "assets/fonts/arcade.ttf"

class PauseScene:
    """Handles the pause screen, UI, and scene transitions."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, scene_manager):
        DebugLogger.section("Initializing Scene: PauseScene")

        self.scene_manager = scene_manager
        self.display = scene_manager.display
        self.draw_manager = scene_manager.draw_manager

        self.ui_elements = []

        # Calculate center position
        center_x = Display.WIDTH // 2
        center_y = Display.HEIGHT // 2

        # --- 1. Pause Title ---
        try:
            self.title_font = pygame.font.Font(FONT_PATH, 100)
        except FileNotFoundError:
            DebugLogger.warn(f"Missing font file at {FONT_PATH}. Using default font.")
            self.title_font = pygame.font.Font(None, 100)

        self.title_surf = self.title_font.render("PAUSED", True, (255, 255, 255))
        self.title_rect = self.title_surf.get_rect(center=(center_x, center_y - 100))

        # --- 2. UI Button ---
        btn_width = 250
        btn_height = 50
        btn_y_start = center_y + 50
        btn_padding = 80

        # Resume Button
        self.resume_button = UIButton(
            x=center_x - btn_width // 2,
            y=btn_y_start,
            width=btn_width,
            height=btn_height,
            action="resume_game",
            color=(80, 150, 200),
            hover_color=(100, 180, 230),
            pressed_color=(60, 120, 160),
            text="Resume",
            font_size=30,
            text_color=(255, 255, 255),
        )

        # Main Menu Button
        self.main_menu_button = UIButton(
            x=center_x - btn_width // 2,
            y=btn_y_start + btn_padding,
            width=btn_width,
            height=btn_height,
            action="main_menu",
            color=(80, 150, 200),
            hover_color=(100, 180, 230),
            pressed_color=(60, 120, 160),
            text="Main Menu",
            font_size=30,
            text_color=(255, 255, 255),
        )

        self.ui_elements.append(self.resume_button)
        self.ui_elements.append(self.main_menu_button)

        DebugLogger.section("- Finished Initialization", only_title=True)