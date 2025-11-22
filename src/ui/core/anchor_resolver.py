"""
anchor_resolver.py
------------------
Resolves element positions from anchors, offsets, and parent relationships.
"""

import pygame
from typing import Tuple, Optional, Union, List


class AnchorResolver:
    """Resolves ui element positions from various anchor modes."""

    _ALIGNMENT_MULTIPLIERS = {
        'top_left': (0, 0), 'top_center': (0.5, 0), 'top': (0.5, 0), 'top_right': (1, 0),
        'center_left': (0, 0.5), 'left': (0, 0.5), 'center': (0.5, 0.5),
        'center_right': (1, 0.5), 'right': (1, 0.5),
        'bottom_left': (0, 1), 'bottom_center': (0.5, 1), 'bottom': (0.5, 1), 'bottom_right': (1, 1),
    }

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

    def _calculate_rect_anchor(self, rect: pygame.Rect, position: str) -> Tuple[int, int]:
        """Calculate anchor point on a rectangle."""
        mult = self._ALIGNMENT_MULTIPLIERS.get(position, (0, 0))
        return int(rect.x + rect.width * mult[0]), int(rect.y + rect.height * mult[1])

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

    def _get_element_alignment(self, anchor, elem_width: int, elem_height: int, element_align: str = None) -> Tuple[
        int, int]:
        """
        Get element alignment offset based on anchor type or explicit alignment.

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
        if element_align:
            position = element_align
        elif isinstance(anchor, str):
            if anchor.startswith('#'):
                position = 'center'
            else:
                position = anchor.replace('parent_', '')
        else:
            # Percentage anchors default to center
            position = 'center'

        # Use shared multipliers
        mult = self._ALIGNMENT_MULTIPLIERS.get(position, (0.5, 0.5))
        return int(elem_width * mult[0]), int(elem_height * mult[1])
