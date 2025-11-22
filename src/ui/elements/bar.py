"""
bar.py
------
Progress/health bar element with gradient and binding support.
"""

import pygame
from typing import Tuple, Optional, Dict, List

from ..core.ui_element import UIElement
from ..core.ui_loader import register_element


@register_element('bar')
class UIBar(UIElement):
    """Visual bar for displaying progress, health, etc."""

    def __init__(self, config):
        """
        Initialize bar.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Bar properties
        self.max_value = config.get('max_value', 100)
        self.current_value = config.get('current_value', self.max_value)
        self._max_value_valid = self.max_value > 0

        # Visual
        self.fill_color = self._parse_color(config.get('color', [0, 255, 0]))
        self.bg_color = self._parse_color(config.get('background', [50, 50, 50]))

        # Gradient configuration
        self.gradient_config = config.get('gradient')

        # Label
        self.show_label = config.get('show_label', False)
        self.label_text = config.get('label', '')
        self._label_font = pygame.font.Font(None, 20) if self.show_label else None

        # Direction
        self.direction = config.get('direction', 'horizontal')  # horizontal, vertical

        # Animation
        self.animated = config.get('animated', True)
        self.visual_value = self.current_value  # Smooth interpolation value
        self.anim_speed = config.get('anim_speed', 5.0)

    def update(self, dt: float, mouse_pos: Tuple[int, int], binding_system=None):
        """Update bar state."""
        super().update(dt, mouse_pos, binding_system)

        # Clamp value if binding active (base class already marked dirty)
        if self.bind_path and self.current_value is not None:
            self.current_value = max(0, min(self.max_value, self.current_value))

        # Smooth animation
        if self.animated and abs(self.visual_value - self.current_value) > 0.1:
            self.visual_value += (self.current_value - self.visual_value) * self.anim_speed * dt
            self.mark_dirty()

    def _get_fill_color(self) -> Tuple[int, int, int]:
        """Get fill color (with gradient support)."""
        if not self.gradient_config:
            return self.fill_color

        # Calculate percentage
        percentage = (self.current_value / self.max_value) * 100 if self._max_value_valid else 0

        # Find gradient stops
        stops = sorted(self.gradient_config.items(), key=lambda x: float(x[0]), reverse=True)

        for threshold, color in stops:
            if percentage >= float(threshold):
                return self._parse_color(color)

        # Fallback
        return self.fill_color

    def _build_surface(self) -> pygame.Surface:
        """Build bar surface."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Background
        surf.fill(self.bg_color)

        # Calculate fill amount
        fill_ratio = self.visual_value / self.max_value if self._max_value_valid else 0
        fill_ratio = max(0.0, min(1.0, fill_ratio))

        # Fill bar
        fill_color = self._get_fill_color()

        if self.direction == 'horizontal':
            fill_width = int(self.width * fill_ratio)
            if fill_width > 0:
                fill_rect = pygame.Rect(0, 0, fill_width, self.height)
                pygame.draw.rect(surf, fill_color, fill_rect)
        else:  # vertical
            fill_height = int(self.height * fill_ratio)
            if fill_height > 0:
                fill_y = self.height - fill_height
                fill_rect = pygame.Rect(0, fill_y, self.width, fill_height)
                pygame.draw.rect(surf, fill_color, fill_rect)

        # Border
        if self.border > 0:
            if self.border_radius > 0:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(),
                                 self.border, border_radius=self.border_radius)
            else:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        # Label
        if self.show_label and self.label_text:
            text_surf = self._label_font.render(self.label_text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(self.width // 2, self.height // 2))
            surf.blit(text_surf, text_rect)

        return surf