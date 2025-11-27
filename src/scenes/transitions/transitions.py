"""
transitions.py
--------------
Scene transition effects.
"""

import pygame
from src.scenes.transitions.base_transition import BaseTransition
from src.core.runtime.game_settings import Display


class InstantTransition(BaseTransition):
    """No animation - immediate switch."""

    def __init__(self):
        super().__init__(duration=0.0)
        self.complete = True

    def update(self, dt: float) -> bool:
        return True

    def draw(self, draw_manager, old_scene, new_scene):
        if new_scene:
            new_scene.draw(draw_manager)


class FadeTransition(BaseTransition):
    """Fade old scene → color → new scene."""

    def __init__(self, duration: float = 0.5, color=(0, 0, 0)):
        super().__init__(duration)
        self.color = color
        self._overlay = None
        self._half = duration / 2

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.complete = True
            return True
        return False

    def draw(self, draw_manager, old_scene, new_scene):
        if self._overlay is None:
            self._overlay = pygame.Surface(
                (Display.WIDTH, Display.HEIGHT), pygame.SRCALPHA
            )
            self._solid = pygame.Surface((Display.WIDTH, Display.HEIGHT))
            self._solid.fill(self.color)

        # Phase 1: Fade out old scene
        if self.elapsed < self._half:
            if old_scene:
                old_scene.draw(draw_manager)
            alpha = int((self.elapsed / self._half) * 255)
        # Phase 2: Hold on solid color (new scene draws after transition completes)
        else:
            draw_manager.queue_draw(self._solid, self._solid.get_rect(), layer=0)
            progress = (self.elapsed - self._half) / self._half
            alpha = int((1.0 - progress) * 255)

        self._overlay.fill((*self.color[:3], alpha))
        draw_manager.queue_draw(self._overlay, self._overlay.get_rect(), layer=9999)

    def create_fade_in_overlay(self):
        """Create overlay for post-transition fade-in."""
        overlay = UIFadeOverlay(color=self.color, max_alpha=255)
        overlay.alpha = 255
        overlay.fade_out(speed=500)
        return overlay


class UIFadeOverlay:
    """Overlay for pause/game over screens (not a scene transition)."""

    def __init__(self, color=(0, 0, 0), max_alpha=180):
        self.surface = pygame.Surface(
            (Display.WIDTH, Display.HEIGHT), pygame.SRCALPHA
        )
        self.color = color
        self.max_alpha = max_alpha
        self.alpha = 0
        self._target = 0
        self._speed = 500

    def fade_in(self, speed=500):
        self._target = self.max_alpha
        self._speed = speed

    def fade_out(self, speed=500):
        self._target = 0
        self._speed = speed

    def update(self, dt: float):
        if self.alpha < self._target:
            self.alpha = min(self.alpha + self._speed * dt, self._target)
        elif self.alpha > self._target:
            self.alpha = max(self.alpha - self._speed * dt, self._target)

    def draw(self, draw_manager):
        if self.alpha > 0:
            self.surface.fill((*self.color[:3], int(self.alpha)))
            draw_manager.queue_draw(self.surface, self.surface.get_rect(), layer=8000)

    @property
    def is_visible(self) -> bool:
        return self.alpha > 0