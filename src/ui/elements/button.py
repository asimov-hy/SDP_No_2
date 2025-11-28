"""
button.py
---------
Interactive button element with hover effects.
"""

import pygame
from typing import Tuple, Optional

from ..core.ui_element import UIElement, GradientColor
from ..core.ui_loader import register_element


@register_element('button')
class UIButton(UIElement):
    """Clickable button with hover and press states."""

    def __init__(self, config):
        """
        Initialize button.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Extract config groups
        graphic_dict = config.get('graphic', config)
        data_dict = config.get('data', config)

        # Button-specific properties
        self.action = data_dict.get('action')
        self.icon = graphic_dict.get('icon')

        # Hover/pressed colors
        self.hover_color = None
        self.pressed_color = None

        if self.hover_config:
            self.hover_color = self._parse_color(self.hover_config.get('color', self.color))
            self.pressed_color = self._parse_color(
                self.hover_config.get('pressed_color', tuple(max(c - 40, 0) for c in self.color[:3]))
            )
        else:
            if isinstance(self.color, GradientColor):
                base_rgb = (100, 100, 100)
            else:
                base_rgb = self.color[:3]

            self.hover_color = tuple(min(c + 30, 255) for c in base_rgb)
            self.pressed_color = tuple(max(c - 40, 0) for c in base_rgb)

            if not isinstance(self.color, GradientColor) and len(self.color) == 4:
                self.hover_color = (*self.hover_color, self.color[3])
                self.pressed_color = (*self.pressed_color, self.color[3])

        # State
        self.is_hovered = False
        self.is_pressed = False
        self.is_focused = False
        self.hover_t = 0.0

        # Transition speed
        self.transition_speed = graphic_dict.get('transition_speed', 8.0)

    def update(self, dt: float, mouse_pos: Tuple[int, int], binding_system=None):
        """Update button state."""
        super().update(dt, mouse_pos, binding_system)

        if not self.enabled or not self.rect:
            self.is_hovered = False
            self.is_pressed = False
            return

        was_hovered = self.is_hovered
        self.is_hovered = mouse_pos != (-1, -1) and self.rect.collidepoint(mouse_pos)

        is_highlighted = self.is_hovered or self.is_focused
        target = 1.0 if is_highlighted else 0.0
        self.hover_t += (target - self.hover_t) * self.transition_speed * dt
        self.hover_t = max(0.0, min(1.0, self.hover_t))

        self.is_pressed = self.is_hovered and pygame.mouse.get_pressed()[0]

        if was_hovered != self.is_hovered or self.hover_t > 0.01:
            self.mark_dirty()

    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """Handle click event."""
        if self.enabled and self.is_hovered:
            return self.action
        return None

    def _build_surface(self) -> pygame.Surface:
        """Build button surface."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        if not self.enabled:
            color = (80, 80, 80)
        elif self.is_pressed:
            color = self.pressed_color
        elif isinstance(self.color, GradientColor):
            color = self._lerp_color((100, 100, 100), self.hover_color, self.hover_t)
        else:
            color = self._lerp_color(self.color, self.hover_color, self.hover_t)

        # Background
        image = self._load_image()
        if image:
            surf.blit(image, (0, 0))
            if self.hover_t > 0.01 or self.is_pressed:
                tint_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                tint_alpha = int(30 * self.hover_t) if not self.is_pressed else 50
                tint_surf.fill((*color, tint_alpha))
                surf.blit(tint_surf, (0, 0))
        elif self.background:
            self._fill_color(surf, self.background)
        else:
            if isinstance(self.color, GradientColor):
                self._fill_color(surf, self.color)
                if self.hover_t > 0.01:
                    tint_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                    base_tint_alpha = int(100 * self.hover_t)
                    tint_colors = []
                    for c in self.color.colors:
                        original_alpha = c[3] if len(c) > 3 else 255
                        scaled_alpha = int((original_alpha / 255) * base_tint_alpha)
                        tint_colors.append((255, 255, 255, scaled_alpha))
                    tint_gradient = GradientColor(colors=tint_colors, direction=self.color.direction)
                    self._fill_color(tint_surf, tint_gradient)
                    surf.blit(tint_surf, (0, 0))
            elif self.border_radius > 0:
                pygame.draw.rect(surf, color, surf.get_rect(), border_radius=self.border_radius)
            else:
                surf.fill(color)

        # Border
        if self.border > 0:
            if self.border_radius > 0:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(),
                                 self.border, border_radius=self.border_radius)
            else:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        # Text (inherited from UIElement)
        if self.text:
            # Handle gradient fallback (gradients don't work on text)
            if isinstance(self.text_color, GradientColor):
                base_color = (255, 255, 255)
            else:
                base_color = self.text_color

            if not self.enabled:
                text_color = tuple(c // 2 for c in base_color[:3])
                if len(base_color) == 4:
                    text_color = (*text_color, base_color[3])
            else:
                text_color = base_color

            text_surf = self.font.render(self.text, True, text_color[:3])
            if len(text_color) == 4:
                text_surf.set_alpha(text_color[3])

            text_rect = self._get_text_position(text_surf, surf.get_rect())
            surf.blit(text_surf, text_rect)

        if self.icon:
            self._draw_icon(surf, self.icon)

        return surf

    def _draw_icon(self, surface: pygame.Surface, icon_type: str):
        """Draw simple vector icon."""
        w, h = surface.get_size()
        color = (255, 255, 255)

        if icon_type == 'close':
            pygame.draw.line(surface, color, (w * 0.3, h * 0.3), (w * 0.7, h * 0.7), 3)
            pygame.draw.line(surface, color, (w * 0.7, h * 0.3), (w * 0.3, h * 0.7), 3)
        elif icon_type == 'pause':
            bar_width = w * 0.15
            bar_height = h * 0.5
            pygame.draw.rect(surface, color, (w * 0.3, h * 0.25, bar_width, bar_height))
            pygame.draw.rect(surface, color, (w * 0.55, h * 0.25, bar_width, bar_height))
        elif icon_type == 'play':
            pygame.draw.polygon(surface, color, [
                (w * 0.3, h * 0.2),
                (w * 0.3, h * 0.8),
                (w * 0.7, h * 0.5)
            ])