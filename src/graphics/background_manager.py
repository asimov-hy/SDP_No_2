"""
background_manager.py
--------------------
Simple scrolling background system with parallax support.
"""

import pygame
from src.core.debug.debug_logger import DebugLogger

# Default background configuration
DEFAULT_BACKGROUND_CONFIG = {
    "layers": [
        {
            "image": "assets/images/maps/test_background.png", # 1536 x1024
            "scroll_speed": [0, -20],
            "parallax": [0.2, 0.4]
        }
    ]
}


class BackgroundLayer:
    """Single scrolling background layer."""

    def __init__(self, image_path, scroll_speed, parallax_factor, screen_size):
        """
        Initialize background layer.

        Args:
            image_path: Path to background image
            scroll_speed: (x, y) pixels per second
            parallax_factor: (x, y) camera influence (0.0-1.0)
            screen_size: (width, height) of viewport
        """
        self.scroll_speed = pygame.Vector2(scroll_speed)
        self.parallax = pygame.Vector2(parallax_factor)
        self.scroll_offset = pygame.Vector2(0, 0)  # CHANGED: Separate scroll from camera

        self.render_offset_x = 0
        self.render_offset_y = 0

        # Load image
        try:
            self.image = pygame.image.load(image_path).convert_alpha()  # Use convert_alpha for transparency
            DebugLogger.init_sub(f"Loaded background: {image_path}")
        except Exception as e:  # Specific exception to see actual error
            # Fallback: create colored surface
            self.image = pygame.Surface((1536, 1024))
            self.image.fill((30, 30, 60))
            DebugLogger.warn(f"Failed to load {image_path}: {e}, using fallback")

        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.screen_width, self.screen_height = screen_size

    def update(self, dt, player_pos=None):
        """Update scroll position."""
        # Auto-scroll (accumulates over time)
        self.scroll_offset += self.scroll_speed * dt

        # Calculate camera offset (based on current player position, doesn't accumulate)
        camera_x = 0
        camera_y = 0
        if player_pos:
            # Center player position (subtract screen center)
            camera_x = (player_pos[0] - self.screen_width / 2) * self.parallax.x
            camera_y = - (player_pos[1] - self.screen_height / 2) * self.parallax.y

        # Combine scroll + camera for final offset
        final_x = (self.scroll_offset.x + camera_x) % self.width
        final_y = (self.scroll_offset.y + camera_y) % self.height

        # Store for rendering
        self.render_offset_x = final_x
        self.render_offset_y = final_y

    def render(self, surface):
        """Draw tiled background to surface."""
        # Calculate how many tiles needed
        tiles_x = (self.screen_width // self.width) + 2
        tiles_y = (self.screen_height // self.height) + 2

        # Starting position (already moduloed in update)
        start_x = -self.render_offset_x
        start_y = -self.render_offset_y

        # Draw tiles
        for tx in range(tiles_x):
            for ty in range(tiles_y):
                x = int(round(start_x + tx * self.width))  # Explicit rounding
                y = int(round(start_y + ty * self.height))
                surface.blit(self.image, (x, y))


class BackgroundManager:
    """Manages multiple scrolling background layers."""

    def __init__(self, screen_size):
        """
        Initialize background manager.

        Args:
            screen_size: (width, height) tuple
        """
        self.screen_size = screen_size
        self.layers = []
        DebugLogger.init_entry("BackgroundManager")

    def add_layer(self, image_path, scroll_speed=(0, 30), parallax=(0.4, 0.6)):
        """
        Add a scrolling layer.

        Args:
            image_path: Path to background image
            scroll_speed: (x, y) scroll speed in px/sec
            parallax: (x, y) camera influence factor
        """
        layer = BackgroundLayer(image_path, scroll_speed, parallax, self.screen_size)
        self.layers.append(layer)
        DebugLogger.init_sub(f"Added layer: speed={scroll_speed}, parallax={parallax}")

    def update(self, dt, player_pos=None):
        """Update all layers."""
        for layer in self.layers:
            layer.update(dt, player_pos)

    def render(self, surface):
        """Render all layers bottom-up."""
        for layer in self.layers:
            layer.render(surface)
