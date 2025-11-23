"""
container.py
------------
Container element that manages child layout.
"""

import pygame
from typing import List, Tuple

from ..core.ui_element import UIElement
from ..core.ui_loader import register_element


@register_element('container')
class UIContainer(UIElement):
    """Container that layouts children automatically."""

    def __init__(self, config):
        """
        Initialize container.

        Args:
            config: Configuration dictionary
        """
        super().__init__(config)

        # Extract config groups (support both old and new format)
        position_dict = config.get('position', config)

        # Layout properties
        self.layout = position_dict.get('layout')
        self.spacing = position_dict.get('spacing', 0)
        self.align = position_dict.get('align', 'start')

        # Children
        self.children: List[UIElement] = []

        # Auto-calculate size if not specified
        self.auto_size = position_dict.get('auto_size', False)

        # Layout batching
        self._layout_pending = False

    def add_child(self, child: UIElement, batch: bool = False):
        """
        Add a child element.

        Args:
            child: Child element to add
            batch: If True, defer layout until commit_layout()
        """
        child.parent = self
        self.children.append(child)

        if batch:
            self._layout_pending = True
        else:
            self._layout_children()
            self.mark_dirty()

    def add_children(self, children: List[UIElement]):
        """
        Add multiple children in one batch.

        Args:
            children: List of child elements to add
        """
        for child in children:
            self.add_child(child, batch=True)
        self.commit_layout()

    def commit_layout(self):
        """Apply pending layout changes."""
        if self._layout_pending:
            self._layout_children()
            self.mark_dirty()
            self._layout_pending = False

    def remove_child(self, child: UIElement, batch: bool = False):
        """
        Remove a child element.

        Args:
            child: Child to remove
            batch: If True, defer layout until commit_layout()
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None

            if batch:
                self._layout_pending = True
            else:
                self._layout_children()
                self.mark_dirty()

    def _layout_children(self):
        """Position children based on layout mode."""
        if not self.children:
            return

        if self.layout == 'vertical':
            self._layout_vertical()
        elif self.layout == 'horizontal':
            self._layout_horizontal()
        elif self.layout == 'grid':
            self._layout_grid()

    def _layout_vertical(self):
        """Stack children vertically."""
        y_offset = self.padding

        for child in self.children:
            # Skip absolutely positioned children
            if child.anchor is not None:
                continue

            # Add top margin
            y_offset += child.margin_top

            # Calculate X based on alignment
            if self.align == 'center':
                x_pos = self.padding + (self.width - self.padding * 2 - child.width) // 2
            elif self.align == 'end':
                x_pos = self.width - self.padding - child.width - child.margin_right
            else:  # start
                x_pos = self.padding + child.margin_left

            # Set layout position
            child._layout_x = x_pos
            child._layout_y = y_offset

            # Advance position
            y_offset += child.height + child.margin_bottom + self.spacing

    def _layout_horizontal(self):
        """Stack children horizontally."""
        x_offset = self.padding

        for child in self.children:
            # Skip absolutely positioned children
            if child.anchor is not None:
                continue

            # Add left margin
            x_offset += child.margin_left

            # Calculate Y based on alignment
            if self.align == 'center':
                y_pos = self.padding + (self.height - self.padding * 2 - child.height) // 2
            elif self.align == 'end':
                y_pos = self.height - self.padding - child.height - child.margin_bottom
            else:  # start
                y_pos = self.padding + child.margin_top

            # Set layout position
            child._layout_x = x_offset
            child._layout_y = y_pos

            # Advance position
            x_offset += child.width + child.margin_right + self.spacing

    def _layout_grid(self):
        """
        Layout children in a grid.

        TODO: Not yet implemented. Planned features:
        - columns: number of columns
        - column_widths: explicit column sizing
        - row_heights: explicit row sizing

        Raises:
            NotImplementedError: Grid layout is not yet implemented
        """
        raise NotImplementedError(
            "Grid layout not yet implemented. Use 'vertical' or 'horizontal' layout instead."
        )

    def update(self, dt: float, mouse_pos: Tuple[int, int], binding_system=None):
        """Update container and children."""
        super().update(dt, mouse_pos, binding_system)

    def _build_surface(self) -> pygame.Surface:
        """Build container surface."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Background
        if self.background:
            surf.fill(self.background)

        # Border
        if self.border > 0:
            if self.border_radius > 0:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(),
                                 self.border, border_radius=self.border_radius)
            else:
                pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border)

        return surf