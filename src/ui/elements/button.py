"""
button.py
---------
Interactive button element with hover effects.
"""

import pygame
from typing import Dict, Tuple, Optional

from ..core.ui_element import UIElement
from ..core.ui_loader import register_element


@register_element('button')
class UIButton(UIElement):
    """Clickable button with hover and press states."""

    _font_cache: Dict[int, pygame.font.Font] = {}

    def __init__(self, config):
        """
        Initialize button.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Button-specific properties
        self.text = config.get('text', '')
        self.action = config.get('action')
        self.icon = config.get('icon')

        # Colors
        self.hover_color = None
        self.pressed_color = None

        if self.hover_config:
            self.hover_color = self._parse_color(self.hover_config.get('color', self.color))
            self.pressed_color = self._parse_color(
                self.hover_config.get('pressed_color', tuple(max(c - 40, 0) for c in self.color))
            )
        else:
            self.hover_color = tuple(min(c + 30, 255) for c in self.color)
            self.pressed_color = tuple(max(c - 40, 0) for c in self.color)

        # State
        self.is_hovered = False
        self.is_pressed = False
        self.hover_t = 0.0  # Hover transition (0-1)

        # Transition speed
        self.transition_speed = config.get('transition_speed', 8.0)

        # Font
        self.font_size = config.get('font_size', 24)
        self.font = self._get_cached_font(self.font_size)

    @classmethod
    def _get_cached_font(cls, size: int) -> pygame.font.Font:
        """Get or create cached font by size."""
        if size not in cls._font_cache:
            cls._font_cache[size] = pygame.font.Font(None, size)
        return cls._font_cache[size]

    def update(self, dt: float, mouse_pos: Tuple[int, int], binding_system=None):
        """Update button state."""
        super().update(dt, mouse_pos, binding_system)

        if not self.enabled or not self.rect:
            self.is_hovered = False
            self.is_pressed = False
            return

        # Check hover state
        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)

        # Smooth hover transition
        target = 1.0 if self.is_hovered else 0.0
        self.hover_t += (target - self.hover_t) * self.transition_speed * dt
        self.hover_t = max(0.0, min(1.0, self.hover_t))

        # Check pressed state
        self.is_pressed = self.is_hovered and pygame.mouse.get_pressed()[0]

        # Mark dirty if state changed
        if was_hovered != self.is_hovered or self.hover_t > 0.01:
            self.mark_dirty()

    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """Handle click event."""
        if self.enabled and self.rect and self.rect.collidepoint(mouse_pos):
            return self.action
        return None

    def _build_surface(self) -> pygame.Surface:
        """Build button surface."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Determine button color based on state
        if not self.enabled:
            color = (80, 80, 80)
        elif self.is_pressed:
            color = self.pressed_color
        else:
            color = self._lerp_color(self.color, self.hover_color, self.hover_t)

        # Background - image takes priority
        image = self._load_image()
        if image:
            surf.blit(image, (0, 0))
            # Apply color tint over image for hover/press states
            if self.hover_t > 0.01 or self.is_pressed:
                tint_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                tint_alpha = int(30 * self.hover_t) if not self.is_pressed else 50
                tint_surf.fill((*color, tint_alpha))
                surf.blit(tint_surf, (0, 0))
        elif self.background:
            surf.fill(self.background)
        else:
            surf.fill(color)

        # Border
        if self.border > 0:
            if self.border_radius > 0:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(),
                                 self.border, border_radius=self.border_radius)
            else:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        # Text
        if self.text:
            text_color = (255, 255, 255) if not self.enabled else (255, 255, 255)
            text_surf = self.font.render(self.text, True, text_color)
            text_rect = self._get_text_position(text_surf, surf.get_rect())
            surf.blit(text_surf, text_rect)

        # Icon (if specified)
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
