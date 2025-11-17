"""
settings_scene.py
-----------------
Settings menu orchestrator - delegates to controllers.
"""

from src.core.runtime.menu_scene import MenuScene
from src.core.debug.debug_logger import DebugLogger


class SettingsScene(MenuScene):
    """Settings menu - placeholder for now."""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        DebugLogger.section("Initializing Scene: SettingsScene")

        # TODO: Add graphics_controller, audio_controller, controls_controller
        # For now, just a stub

        DebugLogger.section("- Finished Initialization", only_title=True)

    def update(self, dt: float):
        """Update settings menu."""
        pass

    def draw(self, draw_manager):
        """Render settings menu."""
        import pygame
        # Placeholder: draw simple text
        surf = pygame.Surface((400, 100))
        surf.fill((50, 50, 50))
        draw_manager.queue_draw(surf, surf.get_rect(center=(640, 360)), layer=0)

    def handle_event(self, event):
        """Handle settings input."""
        import pygame
        # ESC to go back (handled by scene_manager)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE:
            self.scene_manager.set_scene("StartScene")