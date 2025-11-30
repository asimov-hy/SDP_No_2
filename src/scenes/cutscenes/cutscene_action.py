"""
cutscene_action.py
------------------
Base cutscene action and common action library.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Tuple
import pygame

from src.core.runtime.game_settings import Display


class CutsceneAction(ABC):
    """Single cutscene step."""

    def __init__(self, duration: float = 0):
        self.duration = duration
        self.elapsed = 0.0
        self.complete = False

    def on_start(self):
        """Called when action begins."""
        pass

    def on_end(self):
        """Called when action completes."""
        pass

    @abstractmethod
    def update(self, dt: float) -> bool:
        """Update action. Returns True when complete."""
        pass

    def draw(self, draw_manager):
        """Optional draw for visual actions."""
        pass


class ActionGroup(CutsceneAction):
    """Run multiple actions in parallel."""

    def __init__(self, actions: List[CutsceneAction]):
        super().__init__()
        self.actions = actions

    def on_start(self):
        for action in self.actions:
            action.on_start()

    def on_end(self):
        for action in self.actions:
            action.on_end()

    def update(self, dt: float) -> bool:
        all_done = True
        for action in self.actions:
            if not action.complete:
                if action.update(dt):
                    action.complete = True
                else:
                    all_done = False
        return all_done

    def draw(self, draw_manager):
        for action in self.actions:
            action.draw(draw_manager)


class DelayAction(CutsceneAction):
    """Wait for duration."""

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        return self.elapsed >= self.duration


class CallbackAction(CutsceneAction):
    """Execute a function."""

    def __init__(self, callback: Callable, *args, **kwargs):
        super().__init__(duration=0)
        self.callback = callback
        self.args = args
        self.kwargs = kwargs

    def update(self, dt: float) -> bool:
        self.callback(*self.args, **self.kwargs)
        return True


class LockInputAction(CutsceneAction):
    """Enable/disable player input."""

    def __init__(self, player, locked: bool = True):
        super().__init__(duration=0)
        self.player = player
        self.locked = locked

    def update(self, dt: float) -> bool:
        self.player.input_locked = self.locked
        return True


class MoveEntityAction(CutsceneAction):
    """Lerp entity to position."""

    def __init__(self, entity, start_pos: Tuple[float, float],
                 end_pos: Tuple[float, float], duration: float = 1.0,
                 easing: str = "ease_out"):
        super().__init__(duration)
        self.entity = entity
        self.start_pos = pygame.Vector2(start_pos)
        self.end_pos = pygame.Vector2(end_pos)
        self.easing = easing

    def on_start(self):
        self.entity.rect.center = self.start_pos
        self.entity.virtual_pos = pygame.Vector2(self.start_pos)

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1.0)

        # Easing
        if self.easing == "ease_out":
            t = 1 - (1 - t) ** 2
        elif self.easing == "ease_in":
            t = t ** 2
        elif self.easing == "ease_in_out":
            t = t * t * (3 - 2 * t)

        pos = self.start_pos.lerp(self.end_pos, t)
        self.entity.rect.center = pos
        self.entity.virtual_pos = pos

        return self.elapsed >= self.duration


class FadeOverlayAction(CutsceneAction):
    """Fade an overlay in/out."""

    def __init__(self, overlay, target_alpha: int, speed: float = 500):
        super().__init__()
        self.overlay = overlay
        self.target_alpha = target_alpha
        self.speed = speed

    def on_start(self):
        if self.target_alpha > self.overlay.alpha:
            self.overlay.fade_in(speed=self.speed)
        else:
            self.overlay.fade_out(speed=self.speed)
        self.overlay._target = self.target_alpha

    def update(self, dt: float) -> bool:
        self.overlay.update(dt)
        return abs(self.overlay.alpha - self.target_alpha) < 1


class TextFlashAction(CutsceneAction):
    """Display text that fades in/out."""

    def __init__(self, text: str, duration: float = 1.5,
                 fade_in: float = 0.3, fade_out: float = 0.3,
                 font_size: int = 48, color: Tuple[int, int, int] = (255, 255, 255)):
        super().__init__(duration)
        self.text = text
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.font_size = font_size
        self.color = color
        self._surface = None
        self._alpha = 0

    def on_start(self):
        font = pygame.font.Font(None, self.font_size)
        self._surface = font.render(self.text, True, self.color).convert_alpha()
        self._rect = self._surface.get_rect(center=(Display.WIDTH // 2, Display.HEIGHT // 2))

    def update(self, dt: float) -> bool:
        self.elapsed += dt

        # Calculate alpha
        if self.elapsed < self.fade_in:
            self._alpha = int(255 * (self.elapsed / self.fade_in))
        elif self.elapsed > self.duration - self.fade_out:
            remaining = self.duration - self.elapsed
            self._alpha = int(255 * (remaining / self.fade_out))
        else:
            self._alpha = 255

        return self.elapsed >= self.duration

    def draw(self, draw_manager):
        if self._surface and self._alpha > 0:
            temp = self._surface.copy()
            temp.set_alpha(self._alpha)
            draw_manager.queue_draw(temp, self._rect, layer=9000)


class UISlideInAction(CutsceneAction):
    """Slide all HUD elements from their anchor edges."""

    def __init__(self, ui_manager, duration: float = 0.4, stagger: float = 0.05):
        super().__init__(duration + stagger * 20)  # Max duration estimate
        self.ui_manager = ui_manager
        self.duration = duration
        self.stagger = stagger
        self._animations = []

    def on_start(self):
        self.ui_manager.slide_in_hud(self.duration, self.stagger)

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        # Check if all HUD animations complete
        return not self.ui_manager.has_active_hud_animations()