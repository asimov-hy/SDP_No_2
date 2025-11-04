"""
ui_element.py
-------------
Defines the abstract base class for all UI elements.
Every element (buttons, health bars, labels, etc.) inherits from this class
and implements its own behavior and rendering logic.

Responsibilities
----------------
- Define position, size, layer, visibility, and enable state.
- Provide interface methods for updating, handling clicks, and rendering.
"""

import pygame
from src.core.utils.debug_logger import DebugLogger

class UIElement:
    """Base class for all UI components."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, width, height, layer=100):
        """
        Initialize a generic UI element.

        Args:
            x (int): Top-left x position.
            y (int): Top-left y position.
            width (int): Element width in pixels.
            height (int): Element height in pixels.
            layer (int): Draw order; higher layers render on top.
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.layer = layer
        self.visible = True
        self.enabled = True
        # DebugLogger.system(f"Initialized element at ({x}, {y}) | Layer={layer}")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, mouse_pos):
        """
        Update element logic (hover effects, animations, etc.).

        Args:
            mouse_pos (tuple): Current mouse position.
        """
        # DebugLogger.state(f"Updated base element at {self.rect.topleft}")
        pass

    # ===========================================================
    # Event Handling
    # ===========================================================
    def handle_click(self, mouse_pos):
        """
        Return an action string if clicked; otherwise None.

        Args:
            mouse_pos (tuple): Mouse click position.

        Returns:
            str | None: Action identifier or None if not clicked.
        """
        # DebugLogger.action(f"Click handled at {mouse_pos}")
        return None

    # ===========================================================
    # Rendering
    # ===========================================================
    def render_surface(self):
        """
        Must be overridden in subclasses.
        Should return a pygame.Surface representing the element’s current state.

        Returns:
            pygame.Surface: Visual representation of the element.
        """
        # DebugLogger.warn("Base render_surface() called directly (not implemented)")
        raise NotImplementedError