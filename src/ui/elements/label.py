"""
label.py
--------
Text label element with formatting and binding support.
"""

import pygame
from typing import Tuple, Optional, Any

from ..core.ui_element import UIElement
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

        # Text properties
        self.text = config.get('text', '')
        self.format = config.get('format', '{}')  # Format string for bound values

        # Font
        self.font_size = config.get('font_size', 24)
        self.font = pygame.font.Font(None, self.font_size)

        # Text color
        text_color = config.get('text_color') or config.get('color', [255, 255, 255])
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

        # Render text
        text_surf = self.font.render(display_text, True, self.text_color)

        # Create surface
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Background
        if self.background:
            surf.fill(self.background)

        # Position text using base class helper
        text_rect = self._get_text_position(text_surf, surf.get_rect())
        surf.blit(text_surf, text_rect)

        # Border
        if self.border > 0:
            pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        return surf