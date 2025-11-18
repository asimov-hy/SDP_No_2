"""
ui_element.py
-------------
Base class for all ui elements with surface caching and dirty flag optimization.
"""

import pygame
from typing import Optional, Dict, Any, List, Tuple
from src.core.runtime.game_settings import Layers


class UIElement:
    """Base ui element with cached rendering and position management."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ui element from config dictionary.

        Args:
            config: Configuration dictionary from YAML or code
        """
        # Identity
        self.id = config.get('id')
        self.type = config.get('type')

        # Position (resolved later by anchor system)
        self.anchor = config.get('anchor')
        self.offset = config.get('offset', [0, 0])
        self.align = config.get('align', None)
        self.position_mode = config.get('position')  # 'absolute' or None

        self.text_align = config.get('text_align', 'center')

        # Explicit position (for absolute mode)
        self.x = config.get('x', 0)
        self.y = config.get('y', 0)

        # Size
        self.width = config.get('width', 100)
        self.height = config.get('height', 50)
        size = config.get('size')
        if size:
            self.width, self.height = size

        # Spacing (for layout children)
        self.margin = config.get('margin', 0)
        self.margin_top = config.get('margin_top', self.margin)
        self.margin_bottom = config.get('margin_bottom', self.margin)
        self.margin_left = config.get('margin_left', self.margin)
        self.margin_right = config.get('margin_right', self.margin)

        self.padding = config.get('padding', 0)

        # Visual properties
        self.color = self._parse_color(config.get('color', [100, 100, 100]))
        self.alpha = self._parse_alpha(config.get('alpha', 255))
        self.background = self._parse_color(config.get('background')) if config.get('background') else None

        # Border
        self.border = config.get('border', 0)
        self.border_color = self._parse_color(config.get('border_color', [255, 255, 255]))
        self.border_radius = config.get('border_radius', 0)

        # State
        self.visible = config.get('visible', True)
        self.enabled = config.get('enabled', True)
        self.layer = config.get('layer', Layers.UI)

        # Bindings
        self.bind_path = config.get('bind')

        # Effects
        self.hover_config = config.get('hover', {})
        self.fade_config = config.get('fade')

        # Animation state
        self.animations = []

        # Caching
        self._surface_cache: Optional[pygame.Surface] = None
        self._dirty = True
        self.rect: Optional[pygame.Rect] = None

        # Layout state (set by parent container)
        self._layout_x = 0
        self._layout_y = 0

        # Parent reference
        self.parent: Optional['UIElement'] = None

    def _parse_color(self, color) -> Optional[Tuple[int, ...]]:
        """Parse color from various formats."""
        if color is None:
            return None

        if isinstance(color, str):
            # Hex color
            if color.startswith('#'):
                color = color.lstrip('#')
                if len(color) == 6:
                    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
                elif len(color) == 8:
                    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4, 6))

            # Named colors
            named_colors = {
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'white': (255, 255, 255),
                'black': (0, 0, 0),
                'yellow': (255, 255, 0),
                'cyan': (0, 255, 255),
                'magenta': (255, 0, 255),
            }
            return named_colors.get(color.lower(), (255, 255, 255))

        return tuple(color)

    def _parse_alpha(self, alpha) -> int:
        """Parse alpha from float (0.0-1.0) or int (0-255)."""
        if isinstance(alpha, float) and alpha <= 1.0:
            return int(alpha * 255)
        return int(alpha)

    def update(self, dt: float, mouse_pos: Tuple[int, int], binding_system=None):
        """
        Update element state.

        Args:
            dt: Delta time in seconds
            mouse_pos: Current mouse position
            binding_system: System for resolving data bindings
        """
        # Update bindings
        if self.bind_path and binding_system:
            new_value = binding_system.resolve(self.bind_path)
            if new_value is not None and hasattr(self, 'current_value'):
                if self.current_value != new_value:
                    self.current_value = new_value
                    self.mark_dirty()

        # Update animations
        for anim in self.animations[:]:
            if anim.update(dt):
                self.animations.remove(anim)
                self.mark_dirty()

    def handle_click(self, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """
        Handle mouse click.

        Args:
            mouse_pos: Click position

        Returns:
            Action string if element was clicked, None otherwise
        """
        return None

    def render_surface(self) -> pygame.Surface:
        """
        Get rendered surface (cached if not dirty).

        Returns:
            Rendered surface
        """
        if not self._dirty and self._surface_cache:
            return self._surface_cache

        self._surface_cache = self._build_surface()
        self._dirty = False

        return self._surface_cache

    def _build_surface(self) -> pygame.Surface:
        """
        Build the visual surface. Override in subclasses.

        Returns:
            Rendered surface
        """
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Background
        if self.background:
            bg_color = (*self.background[:3], self.alpha if len(self.background) == 3 else self.background[3])
            surf.fill(bg_color)

        # Border
        if self.border > 0:
            if self.border_radius > 0:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(),
                                 self.border, border_radius=self.border_radius)
            else:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        return surf

    def mark_dirty(self):
        """Mark element as needing re-render."""
        self._dirty = True

    def set_visible(self, visible: bool):
        """Set visibility state."""
        if self.visible != visible:
            self.visible = visible
            self.mark_dirty()

    def _lerp_color(self, start: Tuple, end: Tuple, t: float) -> Tuple:
        """Linearly interpolate between two colors."""
        return tuple(int(s + (e - s) * t) for s, e in zip(start, end))

    def _get_text_position(self, text_surf: pygame.Surface, container_rect: pygame.Rect) -> pygame.Rect:
        """
        Get text position based on text_align.

        Args:
            text_surf: Rendered text surface
            container_rect: Container rectangle to align within

        Returns:
            Positioned text rect
        """
        padding = 10  # Padding from edges

        if self.text_align == 'left':
            return text_surf.get_rect(midleft=(padding, container_rect.height // 2))
        elif self.text_align == 'right':
            return text_surf.get_rect(midright=(container_rect.width - padding, container_rect.height // 2))
        else:  # center (default)
            return text_surf.get_rect(center=(container_rect.width // 2, container_rect.height // 2))