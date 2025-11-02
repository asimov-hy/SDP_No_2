"""
display_manager.py
------------------
Handles window management, scaling, and rendering while maintaining
a fixed 16:9 aspect ratio for consistent visuals.

Responsibilities
----------------
- Manage window creation, fullscreen toggling, and resizing.
- Maintain correct scaling and centering for letterboxing.
- Provide screen-to-game coordinate conversions.
- Render the scaled game surface to the window.
"""
import pygame
from src.core.settings import GAME_WIDTH, GAME_HEIGHT
from src.core.utils.debug_logger import DebugLogger

class DisplayManager:
    """Handles window management, scaling, and letterboxing."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, game_width=1280, game_height=720):
        """
        Initialize the display manager and create the main window.

        Args:
            game_width (int): Logical width of the game’s internal surface.
            game_height (int): Logical height of the game’s internal surface.
        """
        self.game_width = game_width
        self.game_height = game_height
        self.game_surface = pygame.Surface((game_width, game_height))

        # Window setup and state tracking
        self.is_fullscreen = False
        self.window = None
        self._create_window()

        # Scale and letterbox offset initialization
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self._calculate_scale()

        DebugLogger.system("DisplayManager", f"Initialized ({game_width}x{game_height}) windowed mode")

    # ===========================================================
    # Window Creation and Scaling
    # ===========================================================
    def _create_window(self, fullscreen=False):
        """
        Create or recreate the display window.

        Args:
            fullscreen (bool): If True, enable fullscreen mode.
        """
        if fullscreen:
            # True fullscreen (fills the entire display)
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.is_fullscreen = True
            DebugLogger.state("DisplayManager", "Switched to fullscreen mode")
        else:
            # Default resizable windowed mode
            self.window = pygame.display.set_mode((self.game_width, self.game_height), pygame.RESIZABLE)
            self.is_fullscreen = False
            DebugLogger.state("DisplayManager", "Switched to windowed mode")

        self._calculate_scale()

    def _calculate_scale(self):
        """Calculate scaling and letterbox offsets to maintain 16:9 aspect ratio."""
        window_width, window_height = self.window.get_size()

        # Calculate scale based on which dimension is the limiting factor
        scale_x = window_width / self.game_width
        scale_y = window_height / self.game_height

        # Use the SMALLER scale to maintain aspect ratio (no stretching)
        self.scale = min(scale_x, scale_y)

        # Calculate scaled dimensions
        scaled_width = int(self.game_width * self.scale)
        scaled_height = int(self.game_height * self.scale)

        # Center the game surface (letterboxing with black bars)
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
        DebugLogger.action("DisplayManager", f"Fullscreen toggled → {state}")

    def handle_resize(self, event):
        """
        Handle window resize events (windowed mode only).

        Args:
            event (pygame.event.Event): Resize event with new width and height.
        """
        if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
            self.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self._calculate_scale()
            DebugLogger.state("DisplayManager", f"Window resized → {event.w}x{event.h}")

    # ===========================================================
    # Rendering
    # ===========================================================
    def get_game_surface(self):
        """
        Get the surface that game objects should draw to.

        Returns:
            pygame.Surface: The logical (unscaled) game surface.
        """
        return self.game_surface

    def render(self):
        """Scale and render the game surface to the actual window with letterboxing."""
        # Clear window with black bars
        self.window.fill((0, 0, 0))

        # Scale game surface and blit to center
        scaled_surface = pygame.transform.scale(self.game_surface, self.scaled_size)
        self.window.blit(scaled_surface, (self.offset_x, self.offset_y))

        pygame.display.flip()

    # ===========================================================
    # Coordinate Utilities
    # ===========================================================
    def screen_to_game_pos(self, screen_x, screen_y):
        """
        Convert screen coordinates (window space) to game-space coordinates.

        Args:
            screen_x (float): X position in window space.
            screen_y (float): Y position in window space.

        Returns:
            tuple[float, float]: Corresponding game-space coordinates.
        """
        game_x = (screen_x - self.offset_x) / self.scale
        game_y = (screen_y - self.offset_y) / self.scale
        return game_x, game_y

    def is_in_game_area(self, screen_x, screen_y):
        """
        Check whether given screen coordinates are inside the game-rendered area.

        Args:
            screen_x (float): X coordinate on the window.
            screen_y (float): Y coordinate on the window.

        Returns:
            bool: True if coordinates fall within the active game area.
        """
        game_x, game_y = self.screen_to_game_pos(screen_x, screen_y)
        return 0 <= game_x <= self.game_width and 0 <= game_y <= self.game_height