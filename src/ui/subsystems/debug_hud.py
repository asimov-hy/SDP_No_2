"""
debug_hud.py
------------
Implements a lightweight developer overlay that provides quick-access debug
controls (fullscreen toggle, exit button, etc.).

Responsibilities
----------------
- Provide developer-facing UI buttons for quick actions.
- Operate independently of scene/UI systems (managed by GameLoop).
- Demonstrate UI button handling, rendering, and state logging.
"""

import pygame

from src.core.utils.debug_logger import DebugLogger
from src.core.settings import Layers
from src.core import settings

from src.ui.button import Button

class DebugHUD:
    """Displays developer buttons for quick debugging actions."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, display_manager):
        """
        Initialize the debug HUD interface.

        Args:
            display_manager: Reference to DisplayManager for toggling fullscreen.
        """
        self.display_manager = display_manager
        self.elements = []
        self.visible = False
        self._last_visibility = self.visible

        self._create_elements()

        DebugLogger.init("║{:<59}║".format(f"\t[DEBUGHUD][INIT]\t→ Initialized"), show_meta=False)

    # ===========================================================
    # Element Creation
    # ===========================================================
    def _create_elements(self):
        """Create the debug HUD buttons (fullscreen toggle + exit)."""
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
            layer=Layers.UI
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
            layer=Layers.UI
        )

        self.elements = [fullscreen_btn, exit_btn]

    # ===========================================================
    # Update Cycle
    # ===========================================================
    def update(self, mouse_pos):
        """
        Update hover states and button animations.

        Args:
            mouse_pos (tuple): Current mouse position in screen coordinates.
        """
        if not self.visible:
            return

        for elem in self.elements:
            elem.update(mouse_pos)

        # Log only when visibility changes
        if self.visible != self._last_visibility:
            self._last_visibility = self.visible

    # ===========================================================
    # Event Handling
    # ===========================================================
    def handle_event(self, event):
        """
        Handle mouse click events for button interaction.

        Args:
            event (pygame.event.Event): Input event from the main loop.
        """
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

    # ===========================================================
    # Button Action Execution
    # ===========================================================
    def _execute_action(self, action):
        """
        Perform the assigned action from a clicked button.

        Args:
            action (str): The action key of the clicked button.
        """
        if action == "toggle_fullscreen":
            self.display_manager.toggle_fullscreen()
            state = "ON" if getattr(self.display_manager, "is_fullscreen", False) else "OFF"
            DebugLogger.action(f"Fullscreen toggled → {state}")

        elif action == "quit":
            DebugLogger.action("Quit requested (GameLoop will terminate)")
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        else:
            DebugLogger.warn(f"Unrecognized button action: {action}")

        return action

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Queue visible elements for rendering.

        Args:
            draw_manager: DrawManager instance used for rendering.
        """
        if not self.visible:
            return

        # --------------------------------------------------------
        # Draw buttons
        # --------------------------------------------------------
        for elem in self.elements:
            if elem.visible:
                draw_manager.queue_draw(elem.render_surface(), elem.rect, elem.layer)

        # --------------------------------------------------------
        # Player Debug Info (global, scene-independent)
        # --------------------------------------------------------
        player = settings.GLOBAL_PLAYER
        if player:
            font = pygame.font.SysFont("consolas", 18)
            pos_text = f"Pos: ({player.rect.x:.1f}, {player.rect.y:.1f})"
            vel_text = f"Vel: ({player.velocity.x:.2f}, {player.velocity.y:.2f})"

            surface_pos = font.render(pos_text, True, (255, 255, 255))
            surface_vel = font.render(vel_text, True, (255, 255, 255))

            # Display near the top-left corner
            rect_pos = surface_pos.get_rect(topleft=(70, 20))
            rect_vel = surface_vel.get_rect(topleft=(70, 40))

            draw_manager.queue_draw(surface_pos, rect_pos, Layers.UI)
            draw_manager.queue_draw(surface_vel, rect_vel, Layers.UI)

    # ===========================================================
    # Visibility Controls
    # ===========================================================
    def toggle(self):
        """Toggle the HUD’s visibility."""
        self.visible = not self.visible
        state = "Shown" if self.visible else "Hidden"
        DebugLogger.action(f"Toggled visibility → {state}")
