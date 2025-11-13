"""
button.py
---------
Defines the Button class — a concrete implementation of UIElement.
A button can display a rectangular shape with optional borders and icons
and can trigger a specific action when clicked.

Responsibilities:
- Handle hover detection and click events.
- Render itself (color, hover state, border, icon) to a pygame.Surface.
"""

"""
POSSIBLIE UPDATES

Current button graphics: Smooth Color Fade (Hover Transition)
    - Button fades into color
    
Optional: Hover Scale (Pop Effect)
    - Buttons enlarge when mouse hovor
    
    Reason: Could be more arcad-y

"""

import pygame
from src.ui.base_ui import BaseUI


class UIButton(BaseUI):
    """Configurable button capable of visual feedback and user interaction."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, width, height, action=None,
                 color=(100, 100, 100), hover_color=None,
                 pressed_color=None, border_color=(255, 255, 255),
                 border_width=2, icon_type=None, layer=100):

        """
        Initialize the button with appearance and behavior parameters.

        Args:
            x (int): X position of the button.
            y (int): Y position of the button.
            width (int): Button width in pixels.
            height (int): Button height in pixels.
            action (str): Action identifier triggered on click.
            color (tuple): Default button color (R, G, B).
            hover_color (tuple): Color when hovered; auto-generated if None.
            pressed_color (tuple): Color when pressed; auto-generated if None.
            border_color (tuple): Border color.
            border_width (int): Thickness of the border (0 = no border).
            icon_type (str): Optional small icon ('close', 'pause', 'play', etc.).
            layer (int): Rendering order layer.
        """
        super().__init__(x, y, width, height, layer)
        self.action = action
        self.color = color
        self.hover_color = hover_color or tuple(min(c + 30, 255) for c in color)
        self.pressed_color = pressed_color or tuple(max(c - 40, 0) for c in color)
        self.border_color = border_color
        self.border_width = border_width
        self.icon_type = icon_type

        # Button state
        self.is_hovered = False
        self.is_pressed = False

        self.hover_t = 0.0  # transition progress (0–1)
        self.transition_speed = 8.0  # higher = faster fade

        self.draw_manager = None

        # DebugLogger.system(f"Initialized at ({x}, {y}) with action '{action}'")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, mouse_pos):
        """
        Update the hover and pressed states based on mouse position.

        Args:
            mouse_pos (tuple): Current mouse position in screen coordinates.
        """
        if not self.enabled:
            self.is_hovered = False
            self.is_pressed = False
            return

        was_hovered = self.is_hovered
        self.is_hovered = self.rect.collidepoint(mouse_pos)

        # Smooth hover interpolation (fade-in/out)
        target = 1.0 if self.is_hovered else 0.0
        self.hover_t += (target - self.hover_t) * self.transition_speed * (1 / 60)
        self.hover_t = max(0.0, min(1.0, self.hover_t))

        # Track pressed state
        self.is_pressed = self.is_hovered and pygame.mouse.get_pressed()[0]

        # Debug logging (commented out for normal builds)
        # if self.is_hovered and not was_hovered:
        #     DebugLogger.state(f"Hover entered for '{self.action}'")
        # elif not self.is_hovered and was_hovered:
        #     DebugLogger.state(f"Hover exited for '{self.action}'")

    def handle_click(self, mouse_pos):
        """
        Return the assigned action string if clicked.

        Args:
            mouse_pos (tuple): Position of the mouse click.

        Returns:
            str | None: The action identifier if clicked, else None.
        """
        if self.enabled and self.rect.collidepoint(mouse_pos):
            # DebugLogger.action(f"Clicked '{self.action}'")
            return self.action
        return None

    # ===========================================================
    # Rendering
    # ===========================================================
    def render_surface(self):
        """
        Create and return a pygame.Surface representing the button’s current state.
        Handles background fill, border, and optional icon rendering.

        Returns:
            pygame.Surface: The rendered button surface.
        """
        surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)

        # Determine color based on state
        if not self.enabled:
            color = (80, 80, 80)
        elif self.is_pressed:
            color = self.pressed_color
        else:
            color = self._lerp_color(self.color, self.hover_color, self.hover_t)

        # Background
        pygame.draw.rect(surf, color, surf.get_rect())

        # Border
        if self.border_width > 0:
            pygame.draw.rect(surf, self.border_color, surf.get_rect(), self.border_width)

        # Icon rendering (from DrawManager or vector fallback)
        if self.icon_type:
            if self.draw_manager:
                icon = self.draw_manager.load_icon(self.icon_type, size=(24, 24))
                rect = icon.get_rect(center=surf.get_rect().center)
                surf.blit(icon, rect)
            else:
                self._draw_icon(surf, self.icon_type, self.border_color)

        # DebugLogger.state(f"Rendered '{self.action}' at {self.rect.topleft}")
        return surf

    # ===========================================================
    # Helper Functions
    # ===========================================================
    def _draw_icon(self, surface, icon_type, color):
        """
        Draw vector-based icons as a fallback when no DrawManager is available.

        Args:
            surface (pygame.Surface): Target surface for drawing.
            icon_type (str): Icon name ('close', 'pause', 'play', 'fullscreen', etc.).
            color (tuple): RGB color of the icon lines.
        """
        w, h = surface.get_size()
        if icon_type == 'close':
            pygame.draw.line(surface, color, (w*0.25, h*0.25), (w*0.75, h*0.75), 3)
            pygame.draw.line(surface, color, (w*0.75, h*0.25), (w*0.25, h*0.75), 3)
        elif icon_type == 'pause':
            bar_width = w * 0.15
            bar_height = h * 0.5
            pygame.draw.rect(surface, color, (w * 0.3, h * 0.25, bar_width, bar_height))
            pygame.draw.rect(surface, color, (w * 0.55, h * 0.25, bar_width, bar_height))
        elif icon_type == 'play':
            pygame.draw.polygon(surface, color, [
                (w * 0.3, h * 0.2),
                (w * 0.3, h * 0.8),
                (w * 0.7, h * 0.5)
            ])
        elif icon_type == 'fullscreen':
            pygame.draw.rect(surface, color, (w*0.2, h*0.2, w*0.6, h*0.6), 3)

    def _lerp_color(self, start, end, t):
        """
        Linearly interpolate between two colors.

        Args:
            start (tuple): Starting color (R, G, B).
            end (tuple): Target color (R, G, B).
            t (float): Interpolation factor between 0.0 and 1.0.

        Returns:
            tuple: Interpolated RGB color.
        """
        return tuple(int(s + (e - s) * t) for s, e in zip(start, end))