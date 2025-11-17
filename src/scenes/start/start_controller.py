"""
start_controller.py
-------------------
Handles start screen logic - menu navigation, title screen animation.
Developer's responsibility - safe to modify.
"""

from src.core.runtime.scene_controller import SceneController
from src.core.debug.debug_logger import DebugLogger


class StartController(SceneController):
    """Manages start screen behavior."""

    def __init__(self, scene):
        super().__init__(scene)
        self.timer = 0.0
        self.auto_skip_delay = 1.0  # Seconds before auto-transition

    def update(self, dt: float):
        """Auto-skip to GameScene after delay."""
        self.timer += dt
        if self.timer > self.auto_skip_delay:
            DebugLogger.system("Auto-transitioning to GameScene")
            self.scene.scene_manager.set_scene("GameScene")

    def handle_event(self, event):
        """Skip to GameScene on any input."""
        import pygame
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            DebugLogger.action("Input detected - skipping to GameScene")
            self.scene.scene_manager.set_scene("GameScene")

    def draw(self, draw_manager):
        """Render placeholder start screen."""
        import pygame
        surf = pygame.Surface((200, 80))
        surf.fill((0, 0, 0))
        draw_manager.queue_draw(surf, surf.get_rect(center=(640, 360)), layer=0)