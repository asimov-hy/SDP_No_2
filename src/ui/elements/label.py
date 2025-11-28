"""
label.py
--------
Text label element with formatting and binding support.
"""

import pygame
from typing import Tuple, Optional, Any

from ..core.ui_element import UIElement, GradientColor
from ..core.ui_loader import register_element


@register_element('label')
class UILabel(UIElement):
    """Text display element."""

    def __init__(self, config):
        """
        Initialize label.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Extract config groups (support both old and new format)
        graphic_dict = config.get('graphic', config)
        data_dict = config.get('data', config)

        # Text properties
        self.text = graphic_dict.get('text', '')
        self.format = data_dict.get('format', '{}')

        # Font
        self.font_size = graphic_dict.get('font_size', 24)
        self.font = self._get_cached_font(self.font_size)

        # Text color (prefer text_color, fallback to color)
        text_color = graphic_dict.get('text_color') or graphic_dict.get('color', [255, 255, 255])
        self.text_color = self._parse_color(text_color)

        # Dynamic text from binding
        self.current_value = None
        self._last_text = None

    def update(self, dt: float, mouse_pos: Tuple[int, int], binding_system=None):
        """Update label state."""
        super().update(dt, mouse_pos, binding_system)

    def _get_display_text(self) -> str:
        """Get the text to display (static or formatted from binding)."""
        if self.current_value is not None:
            try:
                return self.format.format(self.current_value)
            except:
                return str(self.current_value)
        return self.text

    def _build_surface(self) -> pygame.Surface:
        """Build label surface."""
        # Get text to display
        display_text = self._get_display_text()

        # In _build_surface:
        if isinstance(self.text_color, GradientColor):
            text_color_rgb = (255, 255, 255)  # fallback - gradients don't work on text
        else:
            text_color_rgb = self.text_color[:3]

        text_surf = self.font.render(display_text, True, text_color_rgb)

        # Apply alpha if 4th value exists in RGBA
        if not isinstance(self.text_color, GradientColor) and len(self.text_color) == 4:
            text_surf.set_alpha(self.text_color[3])

        # Create surface
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Background
        if self.background:
            self._fill_color(surf, self.background)

        # Position text using base class helper
        text_rect = self._get_text_position(text_surf, surf.get_rect())
        surf.blit(text_surf, text_rect)

        # Border
        if self.border > 0:
            pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        return surf