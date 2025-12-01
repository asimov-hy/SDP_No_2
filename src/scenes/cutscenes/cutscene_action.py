"""
cutscene_action.py
------------------
Base cutscene action and common action library.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Tuple
import pygame
import os

from src.core.runtime.game_settings import Display, Fonts

def _render_text_or_separator(text: str, font, color: Tuple[int, int, int], sep_width: int = 350) -> pygame.Surface:
    """Render text or separator line if text is '---'."""
    if text.strip() == '---':
        surf = pygame.Surface((sep_width, 2), pygame.SRCALPHA)
        surf.fill(color)
        return surf
    return font.render(text, True, color)



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
    """Display text that fades in/out. Supports multi-line with \\n."""

    def __init__(self, text: str, duration: float = 1.5,
                 fade_in: float = 0.3, fade_out: float = 0.3,
                 font_size: int = 48, color: Tuple[int, int, int] = (255, 255, 255),
                 line_spacing: int = 10):
        super().__init__(duration)
        self.text = text
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.font_size = font_size
        self.color = color
        self.line_spacing = line_spacing
        self._surface = None
        self._alpha = 0

    def on_start(self):
        font_path = os.path.join(Fonts.DIR, Fonts.DEFAULT)
        font = pygame.font.Font(font_path, self.font_size)
        lines = self.text.split('\n')

        # Render each line
        line_surfaces = []
        for line in lines:
            line_surfaces.append(_render_text_or_separator(line, font, self.color))

        # Calculate total size
        total_width = max(s.get_width() for s in line_surfaces)
        total_height = sum(s.get_height() for s in line_surfaces) + self.line_spacing * (len(lines) - 1)

        # Create combined surface
        self._surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)

        # Blit lines centered
        y = 0
        for surf in line_surfaces:
            x = (total_width - surf.get_width()) // 2
            self._surface.blit(surf, (x, y))
            y += surf.get_height() + self.line_spacing

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


class TextScaleFadeAction(CutsceneAction):
    """Text that fades in while scaling down from large to normal."""

    def __init__(self, text: str, duration: float = 1.5,
                 start_scale: float = 2.0, end_scale: float = 1.0,
                 font_size: int = 48, color: Tuple[int, int, int] = (255, 255, 255),
                 hold_time: float = 0.5, fade_out: float = 0.3,
                 y_offset: int = 0):
        super().__init__(duration + hold_time + fade_out)
        self.text = text
        self.scale_duration = duration
        self.start_scale = start_scale
        self.end_scale = end_scale
        self.font_size = font_size
        self.color = color
        self.hold_time = hold_time
        self.fade_out = fade_out
        self.y_offset = y_offset
        self._base_surface = None
        self._alpha = 0

    def on_start(self):
        font_path = os.path.join(Fonts.DIR, Fonts.DEFAULT)
        font = pygame.font.Font(font_path, self.font_size)
        self._base_surface = _render_text_or_separator(self.text, font, self.color)

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        total = self.scale_duration + self.hold_time + self.fade_out

        if self.elapsed < self.scale_duration:
            # Scaling phase - fade in
            t = self.elapsed / self.scale_duration
            self._alpha = int(255 * t)
        elif self.elapsed < self.scale_duration + self.hold_time:
            # Hold phase
            self._alpha = 255
        else:
            # Fade out phase
            remaining = total - self.elapsed
            self._alpha = int(255 * (remaining / self.fade_out))

        return self.elapsed >= total

    def draw(self, draw_manager):
        if self._base_surface and self._alpha > 0:
            # Calculate current scale
            if self.elapsed < self.scale_duration:
                t = self.elapsed / self.scale_duration
                t = 1 - (1 - t) ** 2  # ease out
                scale = self.start_scale + (self.end_scale - self.start_scale) * t
            else:
                scale = self.end_scale

            # Scale surface
            w = int(self._base_surface.get_width() * scale)
            h = int(self._base_surface.get_height() * scale)
            if w > 0 and h > 0:
                scaled = pygame.transform.smoothscale(self._base_surface, (w, h))
                scaled.set_alpha(self._alpha)
                rect = scaled.get_rect(center=(Display.WIDTH // 2, Display.HEIGHT // 2 + self.y_offset))
                draw_manager.queue_draw(scaled, rect, layer=9000)


class TextBlinkRevealAction(CutsceneAction):
    """Text that blinks rapidly then slows down to solid (computer boot style)."""

    def __init__(self, text: str, duration: float = 2.0,
                 font_size: int = 48, color: Tuple[int, int, int] = (255, 255, 255),
                 blink_count: int = 12, hold_time: float = 1.0, fade_out: float = 0.3,
                 y_offset: int = 0):
        super().__init__(duration + hold_time + fade_out)
        self.text = text
        self.blink_duration = duration
        self.font_size = font_size
        self.color = color
        self.blink_count = blink_count
        self.hold_time = hold_time
        self.fade_out = fade_out
        self.y_offset = y_offset
        self._surface = None
        self._visible = False
        self._alpha = 255

    def on_start(self):
        font_path = os.path.join(Fonts.DIR, Fonts.DEFAULT)
        font = pygame.font.Font(font_path, self.font_size)
        self._surface = _render_text_or_separator(self.text, font, self.color)
        self._rect = self._surface.get_rect(center=(Display.WIDTH // 2, Display.HEIGHT // 2 + self.y_offset))

    def update(self, dt: float) -> bool:
        self.elapsed += dt
        total = self.blink_duration + self.hold_time + self.fade_out

        if self.elapsed < self.blink_duration:
            # Blink phase - frequency decreases over time (starts fast, slows down)
            t = self.elapsed / self.blink_duration
            # Decelerate blink rate
            freq = 20 * (1 - t ** 1.5) + 2  # starts ~20hz, ends ~2hz
            self._visible = (self.elapsed * freq) % 1.0 > 0.5
            self._alpha = 255
        elif self.elapsed < self.blink_duration + self.hold_time:
            # Solid hold
            self._visible = True
            self._alpha = 255
        else:
            # Fade out
            self._visible = True
            remaining = total - self.elapsed
            self._alpha = int(255 * (remaining / self.fade_out))

        return self.elapsed >= total

    def draw(self, draw_manager):
        if self._surface and self._visible and self._alpha > 0:
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