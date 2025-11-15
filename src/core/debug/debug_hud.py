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

from src.core.runtime import game_settings
from src.core.runtime.game_state import STATE
from src.core.debug.debug_logger import DebugLogger
from src.ui.components.ui_button import UIButton


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

        self.smoothed_fps = 0.0
        self.recent_fps_sum = 0.0
        self.recent_fps_count = 0
        self.min_fps = float('inf')
        self.max_fps = 0.0
        self.min_fps_time = None

        # FPS history buffer for graph
        self.fps_history = []
        self.fps_history_max = 120  # last ~2 seconds at 60fps

        self._create_elements()

        DebugLogger.init_entry("DebugHUD")

    # ===========================================================
    # Element Creation
    # ===========================================================
    def _create_elements(self):
        """Create the debug HUD buttons (fullscreen toggle + exit)."""
        btn_size = 48  # consistent square size
        margin = 10

        fullscreen_btn = UIButton(
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
            layer=game_settings.Layers.UI
        )

        exit_btn = UIButton(
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
            layer=game_settings.Layers.UI
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
        player = STATE.player_ref

        if player:
            font = pygame.font.SysFont("consolas", 18)
            pos_text = f"Pos: ({player.rect.x:.1f}, {player.rect.y:.1f})"
            vel_text = f"Vel: ({player.velocity.x:.2f}, {player.velocity.y:.2f})"

            surface_pos = font.render(pos_text, True, (255, 255, 255))
            surface_vel = font.render(vel_text, True, (255, 255, 255))

            # Display near the top-left corner
            rect_pos = surface_pos.get_rect(topleft=(70, 20))
            rect_vel = surface_vel.get_rect(topleft=(70, 40))

            draw_manager.queue_draw(surface_pos, rect_pos, game_settings.Layers.UI)
            draw_manager.queue_draw(surface_vel, rect_vel, game_settings.Layers.UI)

        # --------------------------------------------------------
        # FPS Metrics: Smoothed / Recent Avg / Min / Max
        # --------------------------------------------------------
        y = 60

        # Recent rolling average
        recent_avg = (
            self.recent_fps_sum / self.recent_fps_count
            if self.recent_fps_count > 0 else 0.0
        )

        # Text lines
        fps_smooth = f"FPS (smoothed): {self.smoothed_fps:.1f}"
        fps_recent = f"Recent Avg FPS: {recent_avg:.1f}"
        fps_min = f"Min FPS: {self.min_fps:.1f} ({self.min_fps_time})" if self.min_fps_time else "Min FPS: --"
        fps_max = f"Max FPS: {self.max_fps:.1f}"

        # Render surfaces
        surface_smooth = font.render(fps_smooth, True, (0, 255, 0))
        surface_recent = font.render(fps_recent, True, (0, 200, 255))
        surface_min = font.render(fps_min, True, (255, 200, 0))
        surface_max = font.render(fps_max, True, (100, 200, 255))

        # Draw
        draw_manager.queue_draw(surface_smooth, surface_smooth.get_rect(topleft=(70, y)), game_settings.Layers.UI)
        draw_manager.queue_draw(surface_recent, surface_recent.get_rect(topleft=(70, y + 20)), game_settings.Layers.UI)
        draw_manager.queue_draw(surface_min, surface_min.get_rect(topleft=(70, y + 40)), game_settings.Layers.UI)
        draw_manager.queue_draw(surface_max, surface_max.get_rect(topleft=(70, y + 60)), game_settings.Layers.UI)

        # # --------------------------------------------------------
        # # FPS Graph (last N frames)
        # # --------------------------------------------------------
        # graph_x = 70
        # graph_y = y + 90
        # bar_width = 2
        # max_height = 40
        #
        # for i, fps in enumerate(self.fps_history):
        #     height = min(120, fps) * (max_height / 120)
        #     rect = pygame.Rect(
        #         graph_x + i * bar_width,
        #         graph_y + (max_height - height),
        #         bar_width,
        #         height
        #     )
        #     draw_manager.queue_draw_rect(rect, (0, 255, 120), game_settings.Layers.UI)

    # ===========================================================
    # Visibility Controls
    # ===========================================================
    def toggle(self):
        """Toggle the HUD’s visibility."""
        self.visible = not self.visible
        state = "Shown" if self.visible else "Hidden"
        DebugLogger.action(f"Toggled visibility → {state}")
