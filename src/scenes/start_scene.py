"""
start_scene.py
--------------
Temporary start screen scene that auto-skips to the main GameScene.
Later, this can be replaced with a full title screen or menu interface.

Responsibilities
----------------
- Initialize the temporary start scene.
- Detect user input or timeout to transition to GameScene.
- Render a placeholder start screen (optional).
"""

import pygame
import sys

from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Display # Reference Display size

from src.ui.components.ui_button import UIButton

FONT_PATH = "assets/fonts/arcade.ttf"

class StartScene:
    """Temporary start scene that auto-transitions to GameScene."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, scene_manager):
        DebugLogger.section("Initializing Scene: StartScene")
        self.scene_manager = scene_manager
        self.display = scene_manager.display
        self.draw_manager = scene_manager.draw_manager
        self.ui_elements = []
        self.timer = 0.0
        DebugLogger.section("- Finished Initialization", only_title=True)
        DebugLogger.section("─"*59+"\n", only_title=True)

        # Calculate center position
        center_x = Display.WIDTH // 2
        center_y = Display.HEIGHT // 2

        # --- 1. Game Title Rendering ---
        try:
            self.title_font = pygame.font.Font(FONT_PATH, 60)
        except FileNotFoundError:
            DebugLogger.warn(f"Missing font file at {FONT_PATH}. Using default font.")
            self.title_font = pygame.font.Font(None, 60)

        self.title_surf = self.title_font.render("202X", True, (255, 255, 255))
        self.title_rect = self.title_surf.get_rect(center=(center_x, center_y - 100))

        # --- 2. UI Button ---
        btn_width = 250
        btn_height = 50
        btn_y_start = center_y + 50
        btn_padding = 80

        # Start Button
        self.start_button = UIButton(
            x = center_x - btn_width // 2,
            y = btn_y_start,
            width = btn_width,
            height = btn_height,
            action = "start_game",
            color = (80, 150, 200),
            hover_color = (100, 180, 230),
            pressed_color = (60, 120, 160),
            text = "Start Game",
            font_size = 30,
            text_color = (255, 255, 255),
        )

        # Exit Button
        self.exit_button = UIButton(
            x=center_x - btn_width // 2,
            y=btn_y_start,
            width=btn_width,
            height=btn_height,
            action="start_game",
            color=(80, 150, 200),
            hover_color=(100, 180, 230),
            pressed_color=(60, 120, 160),
            text="Exit Game",
            font_size=30,
            text_color=(255, 255, 255),
        )

        self.ui_elements.append(self.start_button)
        self.ui_elements.append(self.exit_button)

        DebugLogger.section("- Finished Initialization", only_title=True)
        DebugLogger.section("─" * 59 + "\n", only_title=True)

    # ===========================================================
    # Event Handling
    # ===========================================================
    def handle_event(self, event):
        """
        Detect user input to immediately skip to GameScene.

        Args:
            event (pygame.event.Event): The current Pygame event.
        """
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            DebugLogger.action("Input detected. Ending StartScene")
            self.scene_manager.set_scene("GameScene")

    # ===========================================================
    # Update Logic
    # ===========================================================

    def update(self, dt):
        """
        Update the scene timer and auto-transition after a delay.

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """
        # DebugLogger.init_entry("Starting StartScene")
        self.timer += dt
        if self.timer > 1.0:  # 1 second delay
            DebugLogger.system("Ending StartScene")
            self.scene_manager.set_scene("GameScene")

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render a placeholder start screen surface.

        Args:
            draw_manager: DrawManager instance responsible for rendering.
        """
        # Draw a simple background or message
        surf = pygame.Surface((200, 80))
        surf.fill((0, 0, 0))
        draw_manager.queue_draw(surf, surf.get_rect(center=(640, 360)), layer=0)

    # ===========================================================
    # Lifecycle Hooks
    # ===========================================================
    def on_enter(self):
        DebugLogger.state("on_enter()")

    def on_exit(self):
        DebugLogger.state("on_exit()")

    def on_pause(self):
        DebugLogger.state("on_pause()")

    def on_resume(self):
        DebugLogger.state("on_resume()")

    def reset(self):
        DebugLogger.state("reset()")
