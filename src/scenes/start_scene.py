"""
start_scene.py
--------------
Temporary start screen scene that auto-skips to the main GameScene.
Later, this can be replaced with a real title screen or main menu.
"""

import pygame

class StartScene:
    def __init__(self, scene_manager):
        self.scene_manager = scene_manager
        self.timer = 0.0
        print("[INFO] StartScene: active (temporary auto-skip enabled).")

    def handle_event(self, event):
        """Skip immediately if any key or mouse button is pressed."""
        if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            print("[StartScene] Input detected → switching to GameScene.")
            self.scene_manager.set_scene("game")

    def update(self, dt):
        """Auto-skip after short delay."""
        self.timer += dt
        if self.timer > 1.0:  # 1 second delay
            print("[StartScene] Auto-transition → GameScene.")
            self.scene_manager.set_scene("game")

    def draw(self, draw_manager):
        """Optional placeholder render."""
        # Draw a simple background or message
        surf = pygame.Surface((200, 80))
        surf.fill((0, 0, 0))
        draw_manager.queue_draw(surf, surf.get_rect(center=(640, 360)), layer=0)
