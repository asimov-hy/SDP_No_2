"""
debug_hud.py
------------
Lightweight developer overlay with performance metrics and quick-access controls.
Uses data-driven UI system for buttons, direct rendering for metrics.
"""

import pygame
import time
from src.core.runtime.game_settings import Display, Layers
from src.core.debug.debug_logger import DebugLogger
from src.ui.core.ui_loader import UILoader
from src.ui.core.anchor_resolver import AnchorResolver


class DebugHUD:
    """Developer overlay with metrics and controls."""

    def __init__(self, display_manager, draw_manager):
        """
        Initialize debug HUD with minimal dependencies.

        Args:
            display_manager: DisplayManager for screen coordinate conversion
            draw_manager: DrawManager for rendering
        """
        self.display_manager = display_manager
        self.draw_manager = draw_manager
        self.visible = False

        # Create standalone UI systems
        self.loader = UILoader(ui_manager=None, theme_manager=None)
        self.anchor_resolver = AnchorResolver(Display.WIDTH, Display.HEIGHT)

        # Load UI from config
        self.root_element = None
        self._loaded = False

        # Metrics tracking (always active for performance monitoring)
        self.smoothed_fps = 0.0
        self.recent_fps_sum = 0.0
        self.recent_fps_count = 0
        self.min_fps = float('inf')
        self.max_fps = 0.0
        self.min_fps_time = None

        self.frame_time_history = []
        self.frame_time_history_max = 300
        self.fps_history = []
        self.fps_history_max = 300
        self.current_fps = 0.0

        self.frame_time = 0.0
        self.update_time = 0.0
        self.render_time = 0.0

        # Font for metrics (created once)
        self.font = pygame.font.SysFont("consolas", 14)
        self.font_bold = pygame.font.SysFont("consolas", 14, bold=True)

        DebugLogger.init_entry("DebugHUD")

    def update(self, dt, mouse_pos):
        """
        Update UI elements (only when visible).
        Metrics are tracked regardless of visibility.

        Args:
            dt: Delta time (unused - buttons don't animate)
            mouse_pos: Mouse position in screen coordinates
        """
        if not self.visible or not self.root_element:
            return

        # Convert mouse to game coordinates
        game_pos = self.display_manager.screen_to_game_pos(*mouse_pos)

        # Update UI tree
        self._update_element_tree(self.root_element, dt, game_pos)

    def _update_element_tree(self, element, dt, mouse_pos):
        """Recursively update element and children."""
        if not element.visible:
            return

        element.update(dt, mouse_pos, binding_system=None)

        if hasattr(element, 'children'):
            for child in element.children:
                self._update_element_tree(child, dt, mouse_pos)

    def handle_event(self, event):
        """
        Handle input events for buttons.

        Args:
            event: Pygame event

        Returns:
            Action string if button clicked, None otherwise
        """
        if not self.visible or not self.root_element:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            game_pos = self.display_manager.screen_to_game_pos(*event.pos)
            action = self._handle_click_tree(self.root_element, game_pos)
            if action:
                return self._execute_action(action)

        return None

    def _handle_click_tree(self, element, mouse_pos):
        """Recursively check element tree for clicks."""
        if not element.visible or not element.enabled:
            return None

        # Check this element
        if element.rect and element.rect.collidepoint(mouse_pos):
            action = element.handle_click(mouse_pos)
            if action:
                return action

        # Check children (front to back)
        if hasattr(element, 'children'):
            for child in reversed(element.children):
                action = self._handle_click_tree(child, mouse_pos)
                if action:
                    return action

        return None

    def _execute_action(self, action):
        """Execute button action."""
        if action == "toggle_fullscreen":
            self.display_manager.toggle_fullscreen()
            DebugLogger.action(f"Fullscreen toggled")

        elif action == "quit":
            DebugLogger.action("Quit requested")
            pygame.event.post(pygame.event.Event(pygame.QUIT))

        else:
            DebugLogger.warn(f"Unknown action: {action}")

        return action

    def draw(self, draw_manager, player=None):
        """
        Render debug HUD (only when visible).

        Args:
            draw_manager: DrawManager instance
            player: Optional player reference for debug info
        """
        if not self.visible:
            return

        # Draw UI buttons (from YAML config)
        if self.root_element:
            self._draw_element_tree(self.root_element, draw_manager)

        # Draw metrics (direct rendering for performance)
        self._draw_metrics(draw_manager, player)

    def _draw_element_tree(self, element, draw_manager, parent=None):
        """Recursively draw element tree."""
        if not element.visible:
            return

        # NEW: Only resolve position if cache is invalid
        parent_invalid = parent and not getattr(parent, '_position_cache_valid', True)

        if not getattr(element, '_position_cache_valid', False) or parent_invalid:
            element.rect = self.anchor_resolver.resolve(element, parent)
            element._position_cache_valid = True

        # Render surface
        surface = element.render_surface()

        # Queue for drawing
        # print(f"[DEBUG] Drawing button at layer {Layers.DEBUG}")
        draw_manager.queue_draw(surface, element.rect, Layers.DEBUG)

        # Draw children
        if hasattr(element, 'children'):
            for child in element.children:
                self._draw_element_tree(child, draw_manager, parent=element)

    def _draw_metrics(self, draw_manager, player=None):
        """Draw performance metrics with translucent background."""
        # Background panel (translucent dark)
        panel_width = 280
        panel_height = 180
        panel_x = 10
        panel_y = 10

        bg_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        bg_surface.fill((20, 20, 20, 180))  # Dark translucent
        bg_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        # print(f"[DEBUG] Drawing metrics panel at layer {Layers.DEBUG}")
        draw_manager.queue_draw(bg_surface, bg_rect, Layers.DEBUG)

        # Metrics text
        y_offset = panel_y + 10
        x_offset = panel_x + 10
        line_height = 16

        # Player info (if exists)
        if player:
            self._draw_text(f"Pos: ({player.rect.x:.0f}, {player.rect.y:.0f})",
                           x_offset, y_offset, (150, 255, 150), draw_manager)
            y_offset += line_height

            self._draw_text(f"Vel: ({player.velocity.x:.1f}, {player.velocity.y:.1f})",
                           x_offset, y_offset, (150, 255, 150), draw_manager)
            y_offset += line_height + 5

        # FPS metrics
        recent_avg = (self.recent_fps_sum / self.recent_fps_count
                     if self.recent_fps_count > 0 else 0.0)

        self._draw_text(f"FPS (smooth): {self.smoothed_fps:.1f}",
                       x_offset, y_offset, (100, 255, 100), draw_manager, bold=True)
        y_offset += line_height

        self._draw_text(f"FPS (recent): {recent_avg:.1f}",
                       x_offset, y_offset, (100, 200, 255), draw_manager)
        y_offset += line_height

        min_text = f"Min: {self.min_fps:.1f}"
        if self.min_fps_time:
            min_text += f" ({self.min_fps_time})"
        self._draw_text(min_text, x_offset, y_offset, (255, 200, 100), draw_manager)
        y_offset += line_height

        self._draw_text(f"Max: {self.max_fps:.1f}",
                       x_offset, y_offset, (150, 200, 255), draw_manager)
        y_offset += line_height + 5

        # Frame timing
        self._draw_text(f"Frame: {self.frame_time:.2f}ms",
                       x_offset, y_offset, (255, 255, 150), draw_manager)
        y_offset += line_height

        self._draw_text(f"Update: {self.update_time:.2f}ms",
                       x_offset, y_offset, (200, 255, 200), draw_manager)
        y_offset += line_height

        self._draw_text(f"Render: {self.render_time:.2f}ms",
                       x_offset, y_offset, (200, 200, 255), draw_manager)

    def _draw_text(self, text, x, y, color, draw_manager, bold=False):
        """Helper to render and queue text."""
        font = self.font_bold if bold else self.font
        surface = font.render(text, True, color)
        rect = surface.get_rect(topleft=(x, y))
        draw_manager.queue_draw(surface, rect, Layers.DEBUG)

    def toggle(self):
        self.visible = not self.visible
        if self.visible:
            self._ensure_loaded()
        state = "shown" if self.visible else "hidden"
        DebugLogger.action(f"DebugHUD {state}")

    def record_frame_metrics(self, frame_time_ms: float, scene_time: float, render_time: float, fps: float):
        """
        Record all frame timing metrics. Called once per frame by GameLoop.

        Args:
            frame_time_ms: Total frame time in milliseconds
            scene_time: Scene update time in milliseconds
            render_time: Render pass time in milliseconds
            fps: Current frames per second
        """
        # Core timing
        self.frame_time = frame_time_ms
        self.update_time = scene_time
        self.render_time = render_time

        # Frame time history (for graphs)
        self.frame_time_history.append(frame_time_ms)
        if len(self.frame_time_history) > self.frame_time_history_max:
            self.frame_time_history.pop(0)

        # FPS history (for graphs)
        self.fps_history.append(fps)
        if len(self.fps_history) > self.fps_history_max:
            self.fps_history.pop(0)

        # Smoothed FPS (exponential moving average)
        self.smoothed_fps = (
            self.smoothed_fps * 0.9 + fps * 0.1
            if self.smoothed_fps > 0 else fps
        )

        # Recent average (rolling window)
        self.recent_fps_sum += fps
        self.recent_fps_count += 1
        if self.recent_fps_count > 300:  # 5-second window decay
            self.recent_fps_sum *= 0.5
            self.recent_fps_count = int(self.recent_fps_count * 0.5)

        # Min/Max tracking
        if fps > self.max_fps:
            self.max_fps = fps

        if fps < self.min_fps:
            self.min_fps = fps
            self.min_fps_time = time.strftime("%H:%M:%S")

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True

        try:
            self.root_element = self.loader.load("debug_hud.yaml")
        except FileNotFoundError:
            DebugLogger.warn("debug_hud.yaml not found - using fallback")