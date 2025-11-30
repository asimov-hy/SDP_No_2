"""
ui_element.py
-------------
Base class for all ui elements with surface caching and dirty flag optimization.
"""

import pygame
import os
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
from src.core.runtime.game_settings import Layers, Fonts


@dataclass
class GradientColor:
    """Gradient color with direction and color stops."""
    colors: List[Tuple[int, ...]]
    direction: str = 'horizontal'


class UIElement:
    """Base ui element with cached rendering and position management."""

    _font_cache: Dict[Tuple[str, int], pygame.font.Font] = {}

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ui element from config dictionary.

        Config structure:
            position: {anchor, offset, align, size, margin, padding}
            graphic: {color, alpha, background, image, border, ...}
            data: {bind, format, max_value}
        """
        # Store original config for debugging
        self.config = {'id': config.get('id'), 'type': config.get('type')}

        # Identity
        self.id = config.get('id')
        self.type = config.get('type')

        # Extract grouped configs (support both old and new format)
        position_dict = config.get('position', {})
        graphic_dict = config.get('graphic', {})
        data_dict = config.get('data', {})

        # Legacy support - if no groups, use root level
        if not position_dict and not graphic_dict:
            position_dict = config
            graphic_dict = config
            data_dict = config

        # Store for access by other methods
        self.position_dict = position_dict
        self.graphic_dict = graphic_dict
        self.data_dict = data_dict

        # === POSITION GROUP ===
        self.parent_anchor = position_dict.get('parent_anchor') or position_dict.get('anchor')  # Backwards compat
        self.self_anchor = position_dict.get('self_anchor') or position_dict.get('align', 'top_left')
        self.offset = position_dict.get('offset', [0, 0])
        self.text_align = position_dict.get('text_align', 'center')

        # Size - ONLY from position.size (no width/height)
        size = position_dict.get('size')
        if size:
            self.width, self.height = size
        else:
            # Defer size calculation until image loads
            self.width, self.height = 100, 50  # Temporary defaults
            self._auto_size_from_image = True

        # Spacing
        self.margin = position_dict.get('margin', 0)
        margin_sides = position_dict.get('margin_sides')
        if margin_sides:
            self.margin_top = margin_sides[0]
            self.margin_right = margin_sides[1] if len(margin_sides) > 1 else margin_sides[0]
            self.margin_bottom = margin_sides[2] if len(margin_sides) > 2 else margin_sides[0]
            self.margin_left = margin_sides[3] if len(margin_sides) > 3 else margin_sides[1]
        else:
            self.margin_top = position_dict.get('margin_top', self.margin)
            self.margin_bottom = position_dict.get('margin_bottom', self.margin)
            self.margin_left = position_dict.get('margin_left', self.margin)
            self.margin_right = position_dict.get('margin_right', self.margin)

        self.padding = position_dict.get('padding', 0)

        # Text padding (for text alignment spacing)
        text_padding = position_dict.get('text_padding', 10)
        if isinstance(text_padding, (list, tuple)):
            self.text_padding_left = text_padding[0]
            self.text_padding_right = text_padding[1] if len(text_padding) > 1 else text_padding[0]
        else:
            self.text_padding_left = text_padding
            self.text_padding_right = text_padding

        # === VISUAL GROUP ===
        # Color (can be RGB or RGBA)
        self.color = self._parse_color(graphic_dict.get('color', [100, 100, 100]))

        # Separate alpha for entire element (independent of color's alpha)
        self.alpha = self._parse_alpha(graphic_dict.get('alpha', 255))

        # Background
        background_val = graphic_dict.get('background')
        self.background = self._parse_color(background_val) if background_val else None

        # Image properties
        self.image_path = graphic_dict.get('image')
        self.image_scale = graphic_dict.get('image_scale', 1.0)
        image_tint_val = graphic_dict.get('image_tint')
        self.image_tint = self._parse_color(image_tint_val) if image_tint_val else None
        self._loaded_image = None
        self._draw_manager_ref = None
        self._image_load_attempted = False

        # Border
        self.border = graphic_dict.get('border', 0)
        self.border_color = self._parse_color(graphic_dict.get('border_color', [255, 255, 255]))
        self.border_radius = graphic_dict.get('border_radius', 0)

        # Text properties (used by label, button, etc.)
        self.text = graphic_dict.get('text', '')
        self.font_size = graphic_dict.get('font_size', 24)
        self.font_path = graphic_dict.get('font')  # Optional per-element override
        self.font = self._get_cached_font(self.font_size, self.font_path)
        text_color = graphic_dict.get('text_color', [255, 255, 255])
        self.text_color = self._parse_color(text_color)

        # State (default to true)
        self.visible = graphic_dict.get('visible', True)
        self.enabled = graphic_dict.get('enabled', True)
        self.layer = graphic_dict.get('layer', Layers.UI)

        # Effects
        self.hover_config = graphic_dict.get('hover', {})
        self.fade_config = graphic_dict.get('fade')

        # === DATA GROUP ===
        self.bind_path = data_dict.get('bind')

        # Animation state
        self.animations = []

        # Slide animation state
        self._slide_offset = (0, 0)
        self._slide_start = (0, 0)
        self._slide_end = (0, 0)
        self._slide_elapsed = 0.0
        self._slide_duration = 0.0
        self._slide_delay = 0.0
        self._sliding = False

        self.slide_with_parent = position_dict.get('slide_with_parent', True)

        # Caching
        self._surface_cache: Optional[pygame.Surface] = None
        self._dirty = True
        self.rect: Optional[pygame.Rect] = None
        self._position_cache_valid = False

        # Layout state (set by parent container)
        self._layout_x = 0
        self._layout_y = 0

        # Parent reference
        self.parent: Optional['UIElement'] = None

    @classmethod
    def _get_cached_font(cls, size: int, font_name: str = None) -> pygame.font.Font:
        """Get or create cached font by name and size."""
        if font_name is None:
            font_name = Fonts.DEFAULT

        # Build full path
        font_path = os.path.join(Fonts.DIR, font_name) if font_name else None

        cache_key = (font_path, size)
        if cache_key not in cls._font_cache:
            try:
                cls._font_cache[cache_key] = pygame.font.Font(font_path, size)
            except (FileNotFoundError, pygame.error):
                cls._font_cache[cache_key] = pygame.font.Font(Fonts.FALLBACK, size)
        return cls._font_cache[cache_key]

    def _parse_color(self, color) -> Optional[Union[Tuple[int, ...], GradientColor]]:
        """Parse color from various formats (solid or gradient)."""
        if color is None:
            return None

        # Gradient dict format
        if isinstance(color, dict) and color.get('type') == 'gradient':
            return GradientColor(
                colors=[tuple(c) for c in color.get('colors', [[0, 0, 0], [255, 255, 255]])],
                direction=color.get('direction', 'horizontal')
            )

        if isinstance(color, str):
            # Hex color
            if color.startswith('#'):
                color = color.lstrip('#')
                if len(color) == 6:
                    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))
                elif len(color) == 8:
                    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4, 6))
            return (255, 255, 255)  # fallback for invalid string

        return tuple(color)

    def _parse_alpha(self, alpha) -> int:
        """Parse alpha value."""
        if isinstance(alpha, (int, float)):
            return int(max(0, min(255, alpha)))
        return 255

    def _fill_gradient(self, surface: pygame.Surface, gradient: GradientColor, rect: pygame.Rect = None):
        """Fill surface/rect with gradient colors."""
        rect = rect or surface.get_rect()
        colors = gradient.colors

        if len(colors) < 2:
            surface.fill(colors[0] if colors else (0, 0, 0), rect)
            return

        c1, c2 = colors[0], colors[1]

        if gradient.direction == 'horizontal':
            for x in range(rect.width):
                t = x / max(rect.width - 1, 1)
                r = int(c1[0] + (c2[0] - c1[0]) * t)
                g = int(c1[1] + (c2[1] - c1[1]) * t)
                b = int(c1[2] + (c2[2] - c1[2]) * t)
                a = 255
                if len(c1) > 3 and len(c2) > 3:
                    a = int(c1[3] + (c2[3] - c1[3]) * t)

                pygame.draw.line(surface, (r, g, b, a),
                                 (rect.x + x, rect.y),
                                 (rect.x + x, rect.y + rect.height - 1))
        else:  # vertical
            for y in range(rect.height):
                t = y / max(rect.height - 1, 1)
                r = int(c1[0] + (c2[0] - c1[0]) * t)
                g = int(c1[1] + (c2[1] - c1[1]) * t)
                b = int(c1[2] + (c2[2] - c1[2]) * t)
                a = 255
                if len(c1) > 3 and len(c2) > 3:
                    a = int(c1[3] + (c2[3] - c1[3]) * t)

                pygame.draw.line(surface, (r, g, b, a),
                                 (rect.x, rect.y + y),
                                 (rect.x + rect.width - 1, rect.y + y))

    def _fill_color(self, surface: pygame.Surface, color: Union[Tuple[int, ...], GradientColor],
                    rect: pygame.Rect = None):
        """Fill with either solid color or gradient."""
        if isinstance(color, GradientColor):
            self._fill_gradient(surface, color, rect)
        else:
            if rect:
                surface.fill(color, rect)
            else:
                surface.fill(color)

    def set_draw_manager(self, draw_manager):
        """Store reference to DrawManager for image loading."""
        self._draw_manager_ref = draw_manager

    def _load_image(self):
        """
        Load and cache image from DrawManager.

        Returns:
            pygame.Surface or None
        """
        if self._image_load_attempted:
            return self._loaded_image

        if not self.image_path or not self._draw_manager_ref:
            return None

        self._image_load_attempted = True  # Mark as attempted

        # Return cached if already loaded
        if self._loaded_image:
            return self._loaded_image

        # Check if already in DrawManager cache
        if self.image_path not in self._draw_manager_ref.images:
            # Load with relative path from assets/images/
            full_path = f"assets/images/{self.image_path}"
            self._draw_manager_ref.load_image(self.image_path, full_path, scale=self.image_scale)

        image = self._draw_manager_ref.images.get(self.image_path)

        if not image:
            return None

        # Auto-size from image if needed
        if hasattr(self, '_auto_size_from_image') and self._auto_size_from_image:
            self.width = int(image.get_width())
            self.height = int(image.get_height())
            self._auto_size_from_image = False
            self.invalidate_position()
            self.mark_dirty()

        # Scale to element dimensions
        w, h = max(1, int(self.width)), max(1, int(self.height))
        scaled = pygame.transform.scale(image, (w, h))

        # Apply tint if specified
        if self.image_tint:
            scaled.fill(self.image_tint, special_flags=pygame.BLEND_RGB_MULT)

        self._loaded_image = scaled
        return self._loaded_image

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
        initial_count = len(self.animations)
        self.animations = [anim for anim in self.animations if not anim.update(dt)]
        if len(self.animations) < initial_count:
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
        """Build element surface. Override in subclasses for custom rendering."""
        image = self._load_image()

        # Create surface with updated dimensions
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        if image:
            surf.blit(image, (0, 0))
        elif self.background:
            self._fill_color(surf, self.background)

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
        if self.text_align == 'left':
            return text_surf.get_rect(midleft=(self.text_padding_left, container_rect.height // 2))
        elif self.text_align == 'right':
            return text_surf.get_rect(
                midright=(container_rect.width - self.text_padding_right, container_rect.height // 2))
        else:  # center (default)
            return text_surf.get_rect(center=(container_rect.width // 2, container_rect.height // 2))

    def invalidate_position(self):
        """Mark position as needing recalculation (affects children too)."""
        self._position_cache_valid = False
        # Cascade to children if this is a container
        if hasattr(self, 'children'):
            for child in self.children:
                child.invalidate_position()

    def mark_dirty_with_position(self):
        """Mark both surface and position as invalid."""
        self._dirty = True
        self.invalidate_position()

    # Add after mark_dirty_with_position()

    def show(self):
        """Make element visible."""
        self.set_visible(True)

    def hide(self):
        """Make element invisible."""
        self.set_visible(False)

    def enable(self):
        """Enable element interaction (buttons)."""
        if not self.enabled:
            self.enabled = True
            self.mark_dirty()

    def disable(self):
        """Disable element interaction (visible but not clickable)."""
        if self.enabled:
            self.enabled = False
            self.mark_dirty()

    @property
    def interactive(self):
        """Check if element is both visible and enabled."""
        return self.visible and self.enabled

    @property
    def position(self) -> Tuple[int, int]:
        """
        Get current element position.

        Returns:
            (x, y) tuple based on positioning mode
        """
        if self.rect:
            return (self.rect.x, self.rect.y)
        return (0, 0)

    # ===================================================================
    # Slide Animation
    # ===================================================================

    def start_slide_in(self, offset: Tuple[int, int], duration: float, delay: float = 0):
        """
        Start slide-in animation from offset.

        Args:
            offset: Starting offset from final position (x, y)
            duration: Animation duration
            delay: Delay before starting
        """
        self._slide_start = offset
        self._slide_end = (0, 0)
        self._slide_offset = offset
        self._slide_duration = duration
        self._slide_delay = delay
        self._slide_elapsed = 0.0
        self._sliding = True

    def update_slide(self, dt: float) -> bool:
        """
        Update slide animation.

        Returns:
            True if animation complete
        """
        if not self._sliding:
            return True

        # Handle delay
        if self._slide_delay > 0:
            self._slide_delay -= dt
            return False

        self._slide_elapsed += dt
        t = min(self._slide_elapsed / self._slide_duration, 1.0)

        # Ease-out
        t = 1 - (1 - t) ** 2

        self._slide_offset = (
            int(self._slide_start[0] + (self._slide_end[0] - self._slide_start[0]) * t),
            int(self._slide_start[1] + (self._slide_end[1] - self._slide_start[1]) * t)
        )

        if t >= 1.0:
            self._slide_offset = (0, 0)
            self._sliding = False
            return True

        return False

    @property
    def slide_offset(self) -> Tuple[int, int]:
        """Current slide offset for rendering."""
        return self._slide_offset

    @property
    def is_sliding(self) -> bool:
        return self._sliding
