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

    _font_cache: Dict[int, pygame.font.Font] = {}

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

        # State (default to true)
        self.visible = graphic_dict.get('visible', True)
        self.enabled = graphic_dict.get('enabled', True)
        self.layer = position_dict.get('layer', Layers.UI)

        # Effects
        self.hover_config = graphic_dict.get('hover', {})
        self.fade_config = graphic_dict.get('fade')

        # === DATA GROUP ===
        self.bind_path = data_dict.get('bind')

        # Animation state
        self.animations = []

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
    def _get_cached_font(cls, size: int) -> pygame.font.Font:
        """Get or create cached font by size."""
        if size not in cls._font_cache:
            cls._font_cache[size] = pygame.font.Font(None, size)
        return cls._font_cache[size]

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
        """Parse alpha value."""
        if isinstance(alpha, (int, float)):
            return int(max(0, min(255, alpha)))
        return 255

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
            surf.fill(self.background)

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
