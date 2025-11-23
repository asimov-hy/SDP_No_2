"""
bar.py
------
Progress/health bar element with color thresholds and binding support.
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

        # Extract config groups (support both old and new format)
        graphic_dict = config.get('graphic', config)
        data_dict = config.get('data', config)

        # Bar properties
        self.max_value = data_dict.get('max_value', 100)
        self.current_value = data_dict.get('current_value', self.max_value)
        self._max_value_valid = self.max_value > 0

        # Visual - fill color (prefer 'color' from visual, fallback to base color)
        self.fill_color = self._parse_color(graphic_dict.get('color', [0, 255, 0]))
        self.bg_color = self.background if self.background else self._parse_color([50, 50, 50])

        # Gradient configuration
        self.color_thresholds = graphic_dict.get('color_thresholds')

        # Label
        self.show_label = graphic_dict.get('show_label', False)
        self.label_text = graphic_dict.get('label', '')
        self._label_font = pygame.font.Font(None, 20) if self.show_label else None

        # Direction
        self.direction = graphic_dict.get('direction', 'horizontal')

        # Animation
        self.animated = graphic_dict.get('animated', True)
        self.visual_value = self.current_value
        self.anim_speed = graphic_dict.get('anim_speed', 5.0)

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
        """Get fill color (with threshold-based color switching)."""
        if not self.color_thresholds:
            return self.fill_color

        # Calculate percentage
        percentage = (self.current_value / self.max_value) * 100 if self._max_value_valid else 0

        # Find color threshold stops
        stops = sorted(self.color_thresholds.items(), key=lambda x: float(x[0]), reverse=True)

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