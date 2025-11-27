"""
bar.py
------
Progress/exp bar element with image.
"""

import pygame
from typing import Tuple
from ..core.ui_element import UIElement
from ..core.ui_loader import register_element

@register_element('bar')
class UIBar(UIElement):
    def __init__(self, config):
        super().__init__(config)

        graphic_dict = config.get('graphic')
        if graphic_dict is None: graphic_dict = config
        data_dict = config.get('data')
        if data_dict is None: data_dict = config

        self.max_value = data_dict.get('max_value', 100)
        self.current_value = data_dict.get('current_value', self.max_value)
        self._max_value_valid = self.max_value > 0

        self.fill_color = self._parse_color(graphic_dict.get('color', [0, 255, 0]))
        self.bg_color = self.background if self.background else self._parse_color([50, 50, 50])
        self.color_thresholds = graphic_dict.get('color_thresholds')

        self.show_label = graphic_dict.get('show_label', False)
        self.label_text = graphic_dict.get('label', '')
        self._label_font = pygame.font.Font(None, 20) if self.show_label else None
        self.direction = graphic_dict.get('direction', 'horizontal')
        self.animated = graphic_dict.get('animated', True)
        self.visual_value = self.current_value
        self.anim_speed = graphic_dict.get('anim_speed', 5.0)

    def update(self, dt: float, mouse_pos: Tuple[int, int], binding_system=None):
        super().update(dt, mouse_pos, binding_system)

        if self.bind_path and self.current_value is not None:
            self.current_value = max(0, min(self.max_value, self.current_value))

        if self.animated and abs(self.visual_value - self.current_value) > 0.01:
            self.visual_value += (self.current_value - self.visual_value) * self.anim_speed * dt
            self.mark_dirty()

    def _build_surface(self) -> pygame.Surface:
        image = self._load_image()
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        if self.bg_color:
            surf.fill(self.bg_color)

        fill_ratio = self.visual_value / self.max_value if self._max_value_valid else 0
        fill_ratio = max(0.0, min(1.0, fill_ratio))

        if image:
            if self.direction == 'horizontal':
                fill_width = int(self.width * fill_ratio)
                if fill_width > 0:
                    area = pygame.Rect(0, 0, fill_width, self.height)
                    surf.blit(image, (0, 0), area)
            else:
                fill_height = int(self.height * fill_ratio)
                if fill_height > 0:
                    fill_y = self.height - fill_height
                    area = pygame.Rect(0, fill_y, self.width, fill_height)
                    surf.blit(image, (0, fill_y), area)


        if self.border > 0:
             pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        return surf