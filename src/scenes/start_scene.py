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

from src.core.debug.debug_logger import DebugLogger


class StartScene:
    """Temporary start scene that auto-transitions to GameScene."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, scene_manager):
        DebugLogger.section("Initializing Scene: StartScene")
        self.scene_manager = scene_manager
        self.timer = 0.0
        DebugLogger.section("- Finished Initialization", only_title=True)
        DebugLogger.section("─"*59+"\n", only_title=True)

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
