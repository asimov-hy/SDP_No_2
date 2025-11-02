"""
NOTE: This module is theoretical and can be modified freely.

debug_hud.py
------------
Implements a lightweight developer overlay that provides quick-access debug
controls (fullscreen toggle, exit button, etc.).

Purpose
-------
- Serves as a persistent in-game debug interface.
- Independent of scenes and UI managers (managed directly by GameLoop).
- Demonstrates UI button creation, input handling, and layered rendering.
"""

import pygame

from src.core.utils.debug_logger import DebugLogger

from src.ui.button import Button



class DebugHUD:
    """Displays developer buttons for quick debugging actions."""

    def __init__(self, display_manager):
        """
        Args:
            display_manager: Reference to DisplayManager for toggling fullscreen.
        """
        self.display_manager = display_manager
        self.elements = []
        self.visible = False
        self._last_visibility = self.visible

        self._create_elements()

        DebugLogger.system("DebugHUD", "Initialized")

    # --------------------------------------------------------
    # Initialization
    # --------------------------------------------------------

    def _create_elements(self):
        """Create the debug buttons (fullscreen toggle + exit)."""
        btn_size = 48  # consistent square size
        margin = 10

        fullscreen_btn = Button(
            x=margin,
            y=margin,
            width=btn_size,
            height=btn_size,
            action="toggle_fullscreen",
            color=(80, 150, 200),
            hover_color=(100, 180, 230),
            pressed_color=(60, 120, 160),
            border_color=(255, 255, 255),
            border_width=2,
            icon_type="fullscreen",
            layer=200
        )

        exit_btn = Button(
            x=margin,
            y=margin * 2 + btn_size,
            width=btn_size,
            height=btn_size,
            action="quit",
            color=(200, 50, 50),
            hover_color=(230, 80, 80),
            pressed_color=(160, 40, 40),
            border_color=(255, 255, 255),
            border_width=2,
            icon_type="close",
            layer=200
        )

        self.elements = [fullscreen_btn, exit_btn]

    # --------------------------------------------------------
    # Core Update / Event Handling
    # --------------------------------------------------------

    def update(self, mouse_pos):
        """Update button hover states and animations."""
        if not self.visible:
            return

        for elem in self.elements:
            elem.update(mouse_pos)

        # Log only when visibility changes
        if self.visible != self._last_visibility:
            self._last_visibility = self.visible

    def handle_event(self, event):
        """Handle mouse clicks and execute button actions."""
        if not self.visible:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Convert from window coordinates to internal game-space
            game_x, game_y = self.display_manager.screen_to_game_pos(*event.pos)
            for elem in self.elements:
                action = elem.handle_click((game_x, game_y))
                if action:
                    return self._execute_action(action)
        return None

    # --------------------------------------------------------
    # Button Logic
    # --------------------------------------------------------

    def _execute_action(self, action):
        """Perform the assigned action from a clicked button."""
        if action == "toggle_fullscreen":
            self.display_manager.toggle_fullscreen()
            state = "ON" if getattr(self.display_manager, "is_fullscreen", False) else "OFF"
            DebugLogger.action(
                "DebugHUD",
                f"Fullscreen toggled → {state}"
            )

        elif action == "quit":
            DebugLogger.action(
                "DebugHUD","Quit requested (GameLoop will terminate)")
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        else:
            DebugLogger.warn("DebugHUD", f"Unrecognized button action: {action}")

        return action

    # --------------------------------------------------------
    # Rendering
    # --------------------------------------------------------

    def draw(self, draw_manager):
        """Queue all visible debug UI elements for rendering."""
        if not self.visible:
            return
        for elem in self.elements:
            if elem.visible:
                draw_manager.queue_draw(elem.render_surface(), elem.rect, elem.layer)

    # --------------------------------------------------------
    # Visibility Controls
    # --------------------------------------------------------

    def toggle(self):
        """Toggle the HUD’s visibility."""
        self.visible = not self.visible
        state = "Shown" if self.visible else "Hidden"
        DebugLogger.state("DebugHUD", f"Toggled visibility → {state}")
