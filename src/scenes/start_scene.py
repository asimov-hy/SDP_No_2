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

from src.core.utils.debug_logger import DebugLogger

class StartScene:
    """Temporary start scene that auto-transitions to GameScene."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.timer = 0.0
        DebugLogger.init("║{:<57}║".format(f"\t\t└─ [StartScene][INIT]\t→ Initialized Starting Scene"), show_meta=False)

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
            DebugLogger.action("Input detected → switching to GameScene")
            self.scene_manager.set_scene("GAME")

    # ===========================================================
    # Update Logic
    # ===========================================================

    def update(self, dt):
        """
        Update the scene timer and auto-transition after a delay.

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """
        self.timer += dt
        if self.timer > 1.0:  # 1 second delay
            DebugLogger.action("Auto-transition → GameScene")
            self.scene_manager.set_scene("GAME")

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
