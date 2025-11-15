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
            self.title_font = pygame.font.Font(FONT_PATH, 100)
        except FileNotFoundError:
            DebugLogger.warn(f"Missing font file at {FONT_PATH}. Using default font.")
            self.title_font = pygame.font.Font(None, 100)

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
            y=btn_y_start + btn_padding,
            width=btn_width,
            height=btn_height,
            action="exit_game",
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
        # Needs modification - Set to mouse-click only for now.
        # if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
        #     DebugLogger.action("Input detected. Ending StartScene")
        #
        #     for btn in self.ui_elements:
        #         action = btn.handle_click(event.pos)
        #
        #         if action:
        #             self.on_button_click(action)
        #             break
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:

                for btn in self.ui_elements:
                    action = btn.handle_click(event.pos)

                    if action:
                        self.on_button_click(action)
                        break

    def on_button_click(self, action):
        DebugLogger.action(f"Button triggered action: {action}")

        if action == "start_game":
            self.scene_manager.set_scene("GameScene")
            DebugLogger.system("Starting GameScene")
        elif action == "exit_game":
            DebugLogger.system("Shutting down game")
            pygame.quit()
            sys.exit()
    # ===========================================================
    # Update Logic
    # ===========================================================

    def update(self, dt):
        """
        Update the scene timer and auto-transition after a delay.

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """
        # # DebugLogger.init_entry("Starting StartScene")
        # self.timer += dt
        # if self.timer > 1.0:  # 1 second delay
        #     DebugLogger.system("Ending StartScene")
        #     self.scene_manager.set_scene("GameScene")

        mouse_pos = pygame.mouse.get_pos()
        for btn in self.ui_elements:
            btn.update(mouse_pos)

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
        # surf = pygame.Surface((200, 80))
        # surf.fill((0, 0, 0))
        game_surface = self.display.get_game_surface()
        game_surface.fill((10, 10, 30))

        draw_manager.queue_draw(self.title_surf, self.title_rect, layer = 10)

        for btn in self.ui_elements:
            button_surface = btn.render_surface()
            draw_manager.queue_draw(button_surface, btn.rect, layer = btn.layer)

    # ===========================================================
    # Lifecycle Hooks
    # ===========================================================
    def on_enter(self):
        DebugLogger.state("on_enter() - StartScene")
        pygame.mouse.set_visible(True)

    def on_exit(self):
        DebugLogger.state("on_exit() - StartScene")

    def on_pause(self):
        DebugLogger.state("on_pause()")

    def on_resume(self):
        DebugLogger.state("on_resume()")

    def reset(self):
        DebugLogger.state("reset()")
