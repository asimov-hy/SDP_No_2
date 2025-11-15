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

    # ===========================================================
    # Event Handling
    # ===========================================================
    def handle_event(self, event):
        """
        Detect mouse clicks on UI buttons.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                for btn in self.ui_elements:
                    action = btn.handle_click(event.pos)
                    if action:
                        self.on_button_click(action)
                        break

        def on_button_click(self, action: str):
            DebugLogger.action(f"PauseScene received action: '{action}'")

            if action == "resume_game":
                self.scene_manager.set_scene("GameScene")
                DebugLogger.system("Resuming game")

            elif action == "main_menu":
                DebugLogger.system("Exiting to StartScene")
                self.scene_manager.set_scene("StartScene")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt):
        """
        Update UI elements (e.g., hover states).
        """
        mouse_pos = pygame.mouse.get_pos()
        for btn in self.ui_elements:
            btn.update(mouse_pos)

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render the title and all UI elements.
        """
        # 1. Background change
        overlay = pygame.Surface((Display.WIDTH, Display.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        draw_manager.queue_draw(overlay, (0, 0), layer=90) # Under the UI

        # 2. PAUSED Title
        draw_manager.queue_draw(self.title_surf, self.title_rect, layer=100)

        # 3. UI Buttons
        for btn in self.ui_elements:
            button_surface = btn.render_surface()
            draw_manager.queue_draw(button_surface, btn.rect, layer=btn.layer)

        # ===========================================================
        # Lifecycle Hooks
        # ===========================================================
        def on_enter(self):
            DebugLogger.state("on_enter() - PauseScene")
            pygame.mouse.set_visible(True)

        def on_exit(self):
            DebugLogger.state("on_exit() - PauseScene")

        def on_pause(self):
            DebugLogger.state("on_pause()")

        def on_resume(self):
            DebugLogger.state("on_resume()")

        def reset(self):
            DebugLogger.state("reset()")
