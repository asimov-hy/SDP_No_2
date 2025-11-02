# src/core/display_manager.py
import pygame
from src.core.settings import GAME_WIDTH, GAME_HEIGHT


class DisplayManager:
    """Handles window management, scaling, and borderless fullscreen with fixed 16:9 aspect ratio."""

    def __init__(self, game_width=1280, game_height=720):
        self.game_width = game_width
        self.game_height = game_height
        self.game_surface = pygame.Surface((game_width, game_height))

        self.is_fullscreen = False
        self.window = None
        self._create_window()

        # Calculated values for scaling/letterboxing
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self._calculate_scale()

    def _create_window(self, fullscreen=False):
        """Create or recreate the display window."""
        if fullscreen:
            # True fullscreen - fills entire screen
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.is_fullscreen = True
        else:
            # Default windowed size
            self.window = pygame.display.set_mode((self.game_width, self.game_height), pygame.RESIZABLE)
            self.is_fullscreen = False
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

    def toggle_fullscreen(self):
        """Toggle between windowed and borderless fullscreen mode."""
        self._create_window(not self.is_fullscreen)

    def handle_resize(self, event):
        """Handle window resize events."""
        if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
            self.window = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            self._calculate_scale()

    def get_game_surface(self):
        """Returns the surface that games should draw to."""
        return self.game_surface

    def render(self):
        """Scale and render the game surface to the actual window with letterboxing."""
        # Clear window with black bars
        self.window.fill((0, 0, 0))

        # Scale game surface and blit to center
        scaled_surface = pygame.transform.scale(self.game_surface, self.scaled_size)
        self.window.blit(scaled_surface, (self.offset_x, self.offset_y))

        pygame.display.flip()

    def screen_to_game_pos(self, screen_x, screen_y):
        """Convert screen coordinates to game coordinates."""
        game_x = (screen_x - self.offset_x) / self.scale
        game_y = (screen_y - self.offset_y) / self.scale
        return game_x, game_y

    def is_in_game_area(self, screen_x, screen_y):
        """Check if screen coordinates are within the game area."""
        game_x, game_y = self.screen_to_game_pos(screen_x, screen_y)
        return 0 <= game_x <= self.game_width and 0 <= game_y <= self.game_height