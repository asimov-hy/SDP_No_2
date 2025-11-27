"""
display_manager.py
------------------
Window management, scaling, and rendering with fixed 16:9 aspect ratio.

Responsibilities:
- Window creation and fullscreen toggling
- Aspect ratio preservation with letterboxing
- Screen-to-game coordinate conversion
- Render scaling pipeline
"""

import pygame

from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Display


class DisplayManager:
    """
    Manages window display with software-based scaling.

    Uses CPU-based pygame.transform.scale() for reliable cross-platform behavior.
    Hardware acceleration (pygame.SCALED) was rejected due to inconsistent
    mouse coordinate mapping and platform-dependent behavior.

    Performance: ~2ms overhead per frame at 1080p, acceptable for 2D games.
    """

    # ===========================================================
    # Initialization
    # ===========================================================

    def __init__(self, game_width=1280, game_height=720, window_size="small"):
        """
        Initialize display system.

        Args:
            game_width: Logical game resolution width
            game_height: Logical game resolution height
            window_size: Initial window preset ("small", "medium", "large")
        """
        DebugLogger.init_entry("DisplayManager")

        # Core dimensions
        self.game_width = game_width
        self.game_height = game_height
        self.game_surface = pygame.Surface((game_width, game_height))

        # Window state
        self.window = None
        self.window_size_preset = window_size
        self.is_fullscreen = False

        # Scaling state (calculated in _calculate_scale)
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.scaled_size = (game_width, game_height)

        # Render cache
        self._letterbox_bars = None
        self._scaled_surface_cache = None
        self._display_dirty = True

        # Create initial window
        self._create_window(silent=True)

        mode = "Fullscreen" if self.is_fullscreen else f"Windowed ({game_width}x{game_height})"
        DebugLogger.init_sub(f"Display Mode: {mode}", level=1)

    # ===========================================================
    # Window Management
    # ===========================================================

    def toggle_fullscreen(self):
        """Toggle between windowed and fullscreen modes."""
        self._create_window(fullscreen=not self.is_fullscreen)
        state = "ON" if self.is_fullscreen else "OFF"
        DebugLogger.state(f"Toggled fullscreen → {state}", category="display")

    def set_window_size(self, size_preset: str):
        """
        Change window size to a preset.

        Args:
            size_preset: Preset name ("small", "medium", "large")
        """
        if self.is_fullscreen:
            DebugLogger.warn("Cannot change window size in fullscreen mode")
            return

        if size_preset not in Display.WINDOW_SIZES:
            DebugLogger.warn(f"Unknown window size preset: {size_preset}")
            return

        self.window_size_preset = size_preset
        window_w, window_h = Display.WINDOW_SIZES[size_preset]

        self.window = pygame.display.set_mode(
            (window_w, window_h),
            pygame.DOUBLEBUF | pygame.HWSURFACE
        )
        self._calculate_scale()

        DebugLogger.state(f"Window size changed to {size_preset}: {window_w}x{window_h}")

    def mark_dirty(self):
        """Force display refresh on next render (for external changes)."""
        self._display_dirty = True

    # ===========================================================
    # Rendering Pipeline
    # ===========================================================

    def get_game_surface(self) -> pygame.Surface:
        """Get the logical game surface (always 1280x720)."""
        return self.game_surface

    def render(self):
        """
        Scale and render game surface to window with letterboxing.

        Pipeline:
        1. Refresh letterbox bars if window changed (cached)
        2. Scale game_surface to window size (expensive, ~2ms)
        3. Flip display buffer
        """
        if self._display_dirty:
            self._refresh_display_cache()

        # Scale game surface to cached destination
        pygame.transform.scale(
            self.game_surface,
            self.scaled_size,
            dest_surface=self._scaled_surface_cache
        )

        pygame.display.flip()

    def _refresh_display_cache(self):
        """Rebuild letterbox bars and scaled surface cache."""
        if self._letterbox_bars:
            for surface, position in self._letterbox_bars:
                self.window.blit(surface, position)
        else:
            self.window.fill((0, 0, 0))

        # Cache subsurface to avoid recreation each frame
        cache_rect = pygame.Rect(
            self.offset_x, self.offset_y,
            self.scaled_size[0], self.scaled_size[1]
        )
        self._scaled_surface_cache = self.window.subsurface(cache_rect)
        self._display_dirty = False

    # ===========================================================
    # Coordinate Conversion
    # ===========================================================

    def screen_to_game_pos(self, screen_x: float, screen_y: float) -> tuple:
        """
        Convert window coordinates to game-space coordinates.

        Accounts for letterboxing offset and scale factor.

        Args:
            screen_x: X position in window/physical space
            screen_y: Y position in window/physical space

        Returns:
            (x, y) position in game/logical space
        """
        game_x = (screen_x - self.offset_x) / self.scale
        game_y = (screen_y - self.offset_y) / self.scale
        return game_x, game_y

    def is_in_game_area(self, screen_x: float, screen_y: float) -> bool:
        """
        Check if screen coordinates are inside the game area.

        Returns False for clicks on letterbox bars.
        """
        game_x, game_y = self.screen_to_game_pos(screen_x, screen_y)
        return 0 <= game_x <= self.game_width and 0 <= game_y <= self.game_height

    def get_window_size(self) -> tuple:
        """Get current physical window size in pixels."""
        return self.window.get_size()

    # ===========================================================
    # Internal: Window Creation
    # ===========================================================

    def _create_window(self, fullscreen: bool = False, silent: bool = False):
        """
        Create pygame window with appropriate flags.

        Args:
            fullscreen: Create fullscreen window if True
            silent: Suppress debug logging if True
        """
        if fullscreen:
            self.window = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
            )
            self.is_fullscreen = True
        else:
            window_w, window_h = Display.WINDOW_SIZES.get(
                self.window_size_preset,
                (self.game_width, self.game_height)
            )
            self.window = pygame.display.set_mode(
                (window_w, window_h),
                pygame.DOUBLEBUF | pygame.HWSURFACE
            )
            self.is_fullscreen = False

        self._calculate_scale()

        if not silent:
            if fullscreen:
                mode = "Fullscreen"
            else:
                mode = f"Windowed ({window_w}x{window_h})"
            DebugLogger.init_sub(f"Display Mode: {mode}", level=1)

    # ===========================================================
    # Internal: Scaling Calculations
    # ===========================================================

    def _calculate_scale(self):
        """
        Calculate scale factor and letterbox offsets for aspect ratio preservation.

        Updates: scale, offset_x, offset_y, scaled_size, letterbox_bars
        """
        window_size = self.window.get_size()
        window_width, window_height = window_size

        # Scale to fit while preserving aspect ratio
        scale_x = window_width / self.game_width
        scale_y = window_height / self.game_height
        self.scale = min(scale_x, scale_y)

        # Compute scaled dimensions
        scaled_width = int(self.game_width * self.scale)
        scaled_height = int(self.game_height * self.scale)
        self.scaled_size = (scaled_width, scaled_height)

        # Center in window (creates letterbox effect)
        self.offset_x = (window_width - scaled_width) // 2
        self.offset_y = (window_height - scaled_height) // 2

        # Create letterbox bar surfaces
        self._create_letterbox_bars(window_size)
        self._display_dirty = True

        DebugLogger.trace(
            f"Scale={self.scale:.3f}, Offset=({self.offset_x},{self.offset_y})",
            category="display"
        )

    def _create_letterbox_bars(self, window_size: tuple):
        """
        Create black bar surfaces for letterboxing.

        Pre-creating surfaces is faster than filling the window each frame.

        Args:
            window_size: Current window dimensions (width, height)
        """
        window_width, window_height = window_size

        if self.offset_x > 0:
            # Vertical bars (window wider than 16:9)
            left_bar = pygame.Surface((self.offset_x, window_height))
            right_bar = pygame.Surface((self.offset_x, window_height))
            left_bar.fill((0, 0, 0))
            right_bar.fill((0, 0, 0))

            self._letterbox_bars = [
                (left_bar, (0, 0)),
                (right_bar, (window_width - self.offset_x, 0)),
            ]

        elif self.offset_y > 0:
            # Horizontal bars (window taller than 16:9)
            top_bar = pygame.Surface((window_width, self.offset_y))
            bottom_bar = pygame.Surface((window_width, self.offset_y))
            top_bar.fill((0, 0, 0))
            bottom_bar.fill((0, 0, 0))

            self._letterbox_bars = [
                (top_bar, (0, 0)),
                (bottom_bar, (0, window_height - self.offset_y)),
            ]

        else:
            # Perfect 16:9 — no bars needed
            self._letterbox_bars = None