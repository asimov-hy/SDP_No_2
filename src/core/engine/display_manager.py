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
from src.core.settings import Display
from src.core.utils.debug_logger import DebugLogger


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
        self.game_width = game_width
        self.game_height = game_height
        self.game_surface = pygame.Surface((game_width, game_height))

        # Current window and fullscreen state
        self.is_fullscreen = False
        self.window = None
        self._create_window(silent=True)
        DebugLogger.init("║{:<61}║".format(f"\t[DisplayManager][INIT]\t→ Windowed Mode ({game_width}x{game_height})"), show_meta=False)

        # Calculated values for scaling/letterboxing
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self._calculate_scale()

        self.scaled_surface_cache = None
        self.last_scaled_size = None

    # ===========================================================
    # Window Creation and Scaling
    # ===========================================================
    def _create_window(self, fullscreen=False, silent=False):
        """
        Create or recreate the display window.

        Args:
            fullscreen (bool): If True, enter borderless fullscreen mode.
        """
        if fullscreen:
            # True fullscreen - fills entire screen
            self.window = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
            )
            self.is_fullscreen = True
            if not silent:
                DebugLogger.state("Switched to fullscreen mode")
        else:
            # Default windowed size
            self.window = pygame.display.set_mode(
                (self.game_width, self.game_height),
                pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.HWSURFACE
            )
            self.is_fullscreen = False
            if not silent:
                DebugLogger.state("Switched to windowed mode")

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

        self.scaled_size = (scaled_width, scaled_height)

    # ===========================================================
    # Window Actions
    # ===========================================================
    def toggle_fullscreen(self):
        """Toggle between windowed and fullscreen modes."""
        self._create_window(not self.is_fullscreen)
        state = "ON" if self.is_fullscreen else "OFF"

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
            DebugLogger.state(f"Window resized → {event.w}x{event.h}")

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
        self.window.fill((0, 0, 0))

        # Only rescale if window size changed
        if self.scaled_size != self.last_scaled_size:
            self.scaled_surface_cache = pygame.Surface(self.scaled_size)
            self.last_scaled_size = self.scaled_size

        # Fast blit to cached surface, then to window
        pygame.transform.scale(self.game_surface, self.scaled_size, self.scaled_surface_cache)
        self.window.blit(self.scaled_surface_cache, (self.offset_x, self.offset_y))

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