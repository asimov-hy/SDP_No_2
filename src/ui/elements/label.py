"""
label.py
--------
Text label element with formatting and binding support.
"""

import pygame
from typing import Tuple

from ..core.ui_element import UIElement, GradientColor
from ..core.ui_loader import register_element


@register_element("label")
class UILabel(UIElement):
    """Text display element."""

    def __init__(self, config):
        """
        Initialize label.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Label-specific: format string for bound values
        data_dict = config.get("data", config)
        self.format = data_dict.get("format", "{}")

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
            except:  # noqa: E722
                return str(self.current_value)
        return self.text

    def _build_surface(self) -> pygame.Surface:
        """Build label surface."""
        display_text = self._get_display_text()

        if isinstance(self.text_color, GradientColor):
            text_color_rgb = (255, 255, 255)
        else:
            text_color_rgb = self.text_color[:3]

        text_surf = self.font.render(display_text, True, text_color_rgb)

        if not isinstance(self.text_color, GradientColor) and len(self.text_color) == 4:
            text_surf.set_alpha(self.text_color[3])

        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        if self.background:
            self._fill_color(surf, self.background)

        text_rect = self._get_text_position(text_surf, surf.get_rect())
        surf.blit(text_surf, text_rect)

        if self.border > 0:
            pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        return surf
