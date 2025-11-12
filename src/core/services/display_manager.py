"""
display_manager.py
------------------
Handles all window management, scaling, and rendering operations
while preserving a fixed 16:9 aspect ratio.

Responsibilities
----------------
- Manage window creation and fullscreen toggling.
- Maintain consistent scaling and letterboxing across resolutions.
- Provide coordinate conversions (screen ↔ game space).
- Handle render scaling and resizing behavior.
"""

import pygame
from pygame.display import is_fullscreen

from src.core.debug.debug_logger import DebugLogger


class DisplayManager:
    """Handles window management, scaling, and borderless fullscreen with fixed 16:9 aspect ratio."""

    # ===========================================================
    # Initialization
    # ===========================================================

    def __init__(self, game_width=1280, game_height=720):
        """
        Initialize window, scaling values, and render surface.

        Args:
            game_width (int): Logical game resolution width.
            game_height (int): Logical game resolution height.
        """
        DebugLogger.init_entry("DisplayManager")

        # Core Setup
        self.game_width = game_width
        self.game_height = game_height
        self.game_surface = pygame.Surface((game_width, game_height))

        # Initial state flags
        self.is_fullscreen = False
        self.window = None

        # Window Creation
        self._create_window(silent=True)
        mode = "Fullscreen" if is_fullscreen() else f"Windowed ({game_width}x{game_height})"
        DebugLogger.init_sub(f"Display Mode: {mode}", level=1)

        # Scaling & Letterboxing
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self._calculate_scale()

        # Render Caches
        self.last_scaled_size = None
        self.letterbox_bars = None

    # ===========================================================
    # Window Creation and Scaling
    # ===========================================================
    def _create_window(self, fullscreen=False, silent=False):
        """
        Create or recreate the display window.

        Args:
            fullscreen (bool): If True, enter borderless fullscreen mode.
            silent (bool): Suppress debug output during initialization.
        """
        if fullscreen:
            # True fullscreen - fills entire screen
            self.window = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
            )
            self.is_fullscreen = True
            if not silent:
                DebugLogger.state("Switched to FULLSCREEN mode", category="display")
        else:
            # Default windowed size
            self.window = pygame.display.set_mode(
                (self.game_width, self.game_height),
                pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE
            )
            self.is_fullscreen = False
            if not silent:
                DebugLogger.state(f"Switched to WINDOWED mode ({self.game_width}x{self.game_height})",
                                  category="display")

        self._calculate_scale()

    def _calculate_scale(self):
        """
        Calculate scale factor and letterbox offsets to maintain 16:9 aspect ratio.

        Called when:
        - The window is resized.
        - Fullscreen mode is toggled.
        """
        window_width, window_height = self.window.get_size()

        # Determine scale based on smallest dimension (avoid stretching)
        scale_x = window_width / self.game_width
        scale_y = window_height / self.game_height
        self.scale = min(scale_x, scale_y)

        # Compute scaled dimensions
        scaled_width = int(self.game_width * self.scale)
        scaled_height = int(self.game_height * self.scale)

        # Center the scaled surface (letterboxing with black bars)
        self.offset_x = (window_width - scaled_width) // 2
        self.offset_y = (window_height - scaled_height) // 2

        self._create_letterbox_bars()

        self.scaled_size = (scaled_width, scaled_height)
        DebugLogger.trace(f"Scale={self.scale:.3f}, Offset=({self.offset_x},{self.offset_y})", category="display")

    # ===========================================================
    # Window Actions
    # ===========================================================
    def toggle_fullscreen(self):
        """Toggle between windowed and fullscreen modes."""
        self._create_window(not self.is_fullscreen)
        state = "ON" if self.is_fullscreen else "OFF"
        DebugLogger.state(f"Toggled fullscreen → {state}", category="display")

    def handle_resize(self, event):
        """
        Handle window resize events.

        Args:
            event (pygame.event.Event): The VIDEORESIZE event from pygame.
        """
        if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
            self.window = pygame.display.set_mode(
                (event.w, event.h),
                pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE  # Add flags
            )
            self._calculate_scale()
            DebugLogger.state(f"Window resized → {event.w}x{event.h}", category="display")

    # ===========================================================
    # Rendering Pipeline
    # ===========================================================
    def get_game_surface(self):
        """
        Get the surface that game elements should draw to.

        Returns:
            pygame.Surface: The logical game surface (unscaled).
        """
        return self.game_surface

    def render(self):
        """Scale and render the game surface to the actual window with letterboxing."""
        # Clear window with black bars
        if self.letterbox_bars:
            for surf, pos in self.letterbox_bars:
                self.window.blit(surf, pos)
        else:
            self.window.fill((0, 0, 0))

        # Define target rect on window
        target_rect = pygame.Rect(self.offset_x, self.offset_y,
                                  self.scaled_size[0], self.scaled_size[1])

        # Scale directly to window (no intermediate surface)
        pygame.transform.scale(self.game_surface, self.scaled_size,
                               dest_surface=self.window.subsurface(target_rect))

        pygame.display.flip()

    # ===========================================================
    # Coordinate Utilities
    # ===========================================================
    def screen_to_game_pos(self, screen_x, screen_y):
        """
        Convert window coordinates to game-space coordinates.

        Args:
            screen_x (float): X position in window space.
            screen_y (float): Y position in window space.

        Returns:
            tuple[float, float]: Corresponding position in game coordinates.
        """
        game_x = (screen_x - self.offset_x) / self.scale
        game_y = (screen_y - self.offset_y) / self.scale
        return game_x, game_y

    def is_in_game_area(self, screen_x, screen_y):
        """
        Check if given screen coordinates are inside the game-rendered area.

        Args:
            screen_x (float): X position in window space.
            screen_y (float): Y position in window space.

        Returns:
            bool: True if coordinates are within the active game area.
        """
        game_x, game_y = self.screen_to_game_pos(screen_x, screen_y)
        return 0 <= game_x <= self.game_width and 0 <= game_y <= self.game_height

    def get_window_size(self):
        """
        Get the current window size.

        Returns:
            tuple[int, int]: (width, height) of the actual pygame window.
        """
        return self.window.get_size()

    def _create_letterbox_bars(self):
        """Pre-create black bar surfaces for letterboxing."""
        window_width, window_height = self.window.get_size()

        # Only create bars if there's actual letterboxing
        if self.offset_x > 0:  # Vertical bars (sides)
            self.letterbox_bars = [
                (pygame.Surface((self.offset_x, window_height)), (0, 0)),  # Left
                (pygame.Surface((self.offset_x, window_height)),
                 (window_width - self.offset_x, 0))  # Right
            ]
            for surf, _ in self.letterbox_bars:
                surf.fill((0, 0, 0))
        elif self.offset_y > 0:  # Horizontal bars (top/bottom)
            self.letterbox_bars = [
                (pygame.Surface((window_width, self.offset_y)), (0, 0)),  # Top
                (pygame.Surface((window_width, self.offset_y)),
                 (0, window_height - self.offset_y))  # Bottom
            ]
            for surf, _ in self.letterbox_bars:
                surf.fill((0, 0, 0))
        else:
            self.letterbox_bars = None
