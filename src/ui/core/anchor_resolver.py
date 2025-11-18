"""
anchor_resolver.py
------------------
Resolves element positions from anchors, offsets, and parent relationships.
"""

import pygame
from typing import Tuple, Optional, Union, List


class AnchorResolver:
    """Resolves ui element positions from various anchor modes."""

    def __init__(self, game_width: int, game_height: int):
        """
        Initialize resolver with game dimensions.

        Args:
            game_width: Game logical width
            game_height: Game logical height
        """
        self.game_width = game_width
        self.game_height = game_height
        self.element_registry = {}

    def register_element(self, element_id: str, element):
        """Register element for anchor references."""
        self.element_registry[element_id] = element

    def _find_element_by_id(self, element_id: str):
        """Find element by ID."""
        return self.element_registry.get(element_id)

    def resolve(self, element, parent=None) -> pygame.Rect:
        """
        Calculate final position rectangle for element.

        Args:
            element: UIElement to position
            parent: Parent container (if any)

        Returns:
            Final positioned rect
        """
        # Absolute positioning overrides everything
        if element.position_mode == 'absolute':
            return pygame.Rect(element.x, element.y, element.width, element.height)

        # Calculate anchor point
        anchor_x, anchor_y = self._get_anchor_point(element.anchor, parent, element)

        # Apply offset
        offset_x, offset_y = self._parse_offset(element.offset, element.width, element.height)

        # Apply layout position if set by parent container
        if hasattr(element, '_layout_x') and element.anchor is None:
            # Use layout positioning from parent
            final_x = element._layout_x
            final_y = element._layout_y
        else:
            # Align element based on anchor type or explicit alignment
            element_align = getattr(element, 'align', None)
            align_x, align_y = self._get_element_alignment(
                element.anchor,
                element.width,
                element.height,
                element_align
            )
            final_x = anchor_x + offset_x - align_x
            final_y = anchor_y + offset_y - align_y

        # Apply margins
        final_x += element.margin_left
        final_y += element.margin_top

        return pygame.Rect(int(final_x), int(final_y), element.width, element.height)

    def _get_element_alignment(self, anchor, elem_width: int, elem_height: int, element_align: str = None) -> Tuple[
        int, int]:
        """
        Get element alignment offset based on anchor type or explicit alignment.

        This determines which point of the element aligns to the anchor.

        Args:
            anchor: Anchor specification
            elem_width: Element width
            elem_height: Element height
            element_align: Optional explicit alignment override

        Returns:
            (x, y) offset from element's top-left to alignment point
        """
        if anchor is None:
            return 0, 0

        # Determine position string
        if element_align and element_align != 'center':
            # Use explicit alignment if provided
            position = element_align
        elif isinstance(anchor, str):
            # Otherwise match anchor type
            if anchor.startswith('#'):
                parts = anchor[1:].split(':')
                position = parts[1] if len(parts) > 1 else 'center'
            else:
                # Remove "parent_" prefix if present
                position = anchor.replace('parent_', '')
        else:
            # Percentage anchors default to center alignment
            return elem_width // 2, elem_height // 2

        # Calculate alignment offset based on position
        alignments = {
            'top_left': (0, 0),
            'top_center': (elem_width // 2, 0),
            'top': (elem_width // 2, 0),
            'top_right': (elem_width, 0),
            'center_left': (0, elem_height // 2),
            'left': (0, elem_height // 2),
            'center': (elem_width // 2, elem_height // 2),
            'center_right': (elem_width, elem_height // 2),
            'right': (elem_width, elem_height // 2),
            'bottom_left': (0, elem_height),
            'bottom_center': (elem_width // 2, elem_height),
            'bottom': (elem_width // 2, elem_height),
            'bottom_right': (elem_width, elem_height),
        }

        return alignments.get(position, (elem_width // 2, elem_height // 2))

    def _get_anchor_point(self, anchor, parent, element) -> Tuple[int, int]:
        """
        Get the anchor point coordinates.

        Args:
            anchor: Anchor specification (string, list, or None)
            parent: Parent container
            element: Element being positioned

        Returns:
            (x, y) anchor point
        """
        if anchor is None:
            # No anchor - use top-left or layout position
            if parent and hasattr(element, '_layout_x'):
                return element._layout_x, element._layout_y
            return 0, 0

        if isinstance(anchor, str):
            return self._get_named_anchor(anchor, parent)

        if isinstance(anchor, (list, tuple)):
            return self._get_percentage_anchor(anchor, parent)

        return 0, 0

    def _get_named_anchor(self, name: str, parent) -> Tuple[int, int]:
        """
        Convert named anchor to coordinates.

        Args:
            name: Anchor name (e.g., 'center', 'top_left', 'parent_center')
            parent: Parent container

        Returns:
            (x, y) coordinates
        """

        # Element ID reference (e.g., "#button_id:center")
        if name.startswith('#'):
            parts = name[1:].split(':')
            element_id = parts[0]
            position = parts[1] if len(parts) > 1 else 'center'

            # Find element by ID (need to pass element registry)
            target_element = self._find_element_by_id(element_id)
            if target_element and target_element.rect:
                return self._calculate_rect_anchor(target_element.rect, position)

        # Parent-relative anchors
        if name.startswith('parent_'):
            if not parent or not parent.rect:
                # Fallback to screen anchors if no parent
                return self._get_named_anchor(name.replace('parent_', ''), None)

            parent_anchor = name.replace('parent_', '')
            return self._calculate_rect_anchor(parent.rect, parent_anchor)

        # Screen-relative anchors
        screen_rect = pygame.Rect(0, 0, self.game_width, self.game_height)
        return self._calculate_rect_anchor(screen_rect, name)

    def _calculate_rect_anchor(self, rect: pygame.Rect, position: str) -> Tuple[int, int]:
        """Calculate anchor point on a rectangle."""
        positions = {
            'center': rect.center,
            'top_left': rect.topleft,
            'top_center': rect.midtop,
            'top_right': rect.topright,
            'center_left': rect.midleft,
            'center_right': rect.midright,
            'bottom_left': rect.bottomleft,
            'bottom_center': rect.midbottom,
            'bottom_right': rect.bottomright,
        }

        return positions.get(position, rect.topleft)

    def _get_percentage_anchor(self, anchor: Union[List, Tuple], parent) -> Tuple[int, int]:
        """
        Parse percentage-based anchor.

        Args:
            anchor: [x, y] where values can be percentages or pixels
            parent: Parent container

        Returns:
            (x, y) coordinates
        """
        x_val, y_val = anchor

        # Determine reference dimensions
        if parent and parent.rect:
            ref_width = parent.rect.width
            ref_height = parent.rect.height
            base_x = parent.rect.x
            base_y = parent.rect.y
        else:
            ref_width = self.game_width
            ref_height = self.game_height
            base_x = 0
            base_y = 0

        # Parse X
        x = self._parse_dimension(x_val, ref_width) + base_x

        # Parse Y
        y = self._parse_dimension(y_val, ref_height) + base_y

        return int(x), int(y)

    def _parse_dimension(self, value, reference: int) -> float:
        """
        Parse a dimension value (can be pixel, percentage, or parent percentage).

        Args:
            value: Dimension value (int, float, or string)
            reference: Reference dimension for percentages

        Returns:
            Calculated dimension in pixels
        """
        if isinstance(value, str):
            if '%' in value:
                # Percentage of reference
                percentage = float(value.strip('%')) / 100
                return reference * percentage
            elif value.startswith('parent:'):
                # Parent percentage
                percentage_str = value.replace('parent:', '').strip('%')
                percentage = float(percentage_str) / 100
                return reference * percentage

        return float(value)

    def _parse_offset(self, offset: Union[List, Tuple], elem_width: int, elem_height: int) -> Tuple[int, int]:
        """
        Parse offset values (can be pixels or percentages).

        Args:
            offset: [x, y] offset values
            elem_width: Element width (for percentage calculations)
            elem_height: Element height

        Returns:
            (x, y) offset in pixels
        """
        if not offset:
            return 0, 0

        x_offset, y_offset = offset

        # Parse X offset
        if isinstance(x_offset, str) and '%' in x_offset:
            percentage = float(x_offset.strip('%')) / 100
            x = int(self.game_width * percentage)
        else:
            x = int(x_offset)

        # Parse Y offset
        if isinstance(y_offset, str) and '%' in y_offset:
            percentage = float(y_offset.strip('%')) / 100
            y = int(self.game_height * percentage)
        else:
            y = int(y_offset)

        return x, y
