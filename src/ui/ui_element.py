"""
ui_element.py
-------------
Defines the abstract base class for all UI elements.
Every element (buttons, health bars, labels, etc.) inherits from this class
and implements its own behavior and rendering logic.

Responsibilities:
- Define position, size, layer, visibility, and enable state.
- Provide interface methods for updating, handling clicks, and rendering.
"""

import pygame


class UIElement:
    def __init__(self, x, y, width, height, layer=100):
        """
        Initialize a generic UI element.

        Args:
            x, y: Top-left position of the element.
            width, height: Dimensions of the element.
            layer: Draw order (higher layers are drawn later).
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.layer = layer
        self.visible = True
        self.enabled = True

    def update(self, mouse_pos):
        """Update element logic (hover effects, animations, etc.)."""
        pass

    def handle_click(self, mouse_pos):
        """Return an action string if clicked; otherwise, None."""
        return None

    def render_surface(self):
        """
        Must be overridden in subclasses.
        Should return a pygame.Surface representing the current visual state.
        """
        raise NotImplementedError
