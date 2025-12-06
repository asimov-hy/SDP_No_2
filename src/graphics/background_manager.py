"""
background_manager.py
---------------------
Scrolling background system with parallax support.

Provides multi-layer scrolling backgrounds with:
- Per-layer scroll speeds
- Camera-based parallax effects
- Runtime controls (pause, speed, parallax)
- Seamless tiling
"""

import pygame
import math
import random
from src.core.debug.debug_logger import DebugLogger


class BackgroundLayer:
    """
    Single scrolling background layer.

    Handles auto-scrolling and camera-based parallax for one image layer.
    Automatically tiles to fill the screen.
    """

    __slots__ = (
        "scroll_speed",
        "parallax",
        "scroll_offset",
        "render_offset_x",
        "render_offset_y",
        "image",
        "width",
        "height",
        "screen_width",
        "screen_height",
    )

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
        self.scroll_offset = pygame.Vector2(0, 0)
        self.render_offset_x = 0
        self.render_offset_y = 0

        # Screen dimensions
        self.screen_width, self.screen_height = screen_size

        # Load image
        self._load_image(image_path)

    def _load_image(self, image_path):
        """
        Load background image with fallback.

        Args:
            image_path: Path to image file
        """
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            DebugLogger.init_sub(f"Loaded background: {image_path}")
        except Exception as e:
            # Fallback: create colored surface
            self.image = pygame.Surface((1536, 1024))
            self.image.fill((30, 30, 60))
            DebugLogger.warn(f"Failed to load {image_path}: {e}, using fallback")

        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def random_scatter_objects(self, object_paths, count, min_distance=50, max_attempts=50):
        """
            Scatters objects onto the background layer.

            1. Maintains the original image size without scaling.
            2. Ensures a minimum separation distance (min_distance) from existing objects.
            3. Calculates distance considering the map's seamless wrapping (Toroidal Check).

            Args:
                object_paths (list): List of image file paths.
                count (int): Target number of objects to place.
                min_distance (int): Minimum distance between objects (in pixels).
                max_attempts (int): Maximum number of retries if position selection fails.
            """
        if not object_paths:
            return

        DebugLogger.init_sub(f"Scattering objects with dist_check={min_distance}...")

        loaded_objs = []

        for path in object_paths:
            img = pygame.image.load(path).convert_alpha()
            loaded_objs.append(img)

        if not loaded_objs:
            return

        placed_positions = []

        for _ in range(count):
            img = random.choice(loaded_objs)
            angle = random.uniform(0, 360)
            img = pygame.transform.rotate(img, angle)

            w, h = img.get_size()

            valid_pos = False
            best_x, best_y = 0, 0

            for attempt in range(max_attempts):
                cx = random.randint(0, self.width - 1)
                cy = random.randint(0, self.height - 1)

                # Distance Check
                conflict = False
                for (px, py) in placed_positions:
                    dx = abs(cx - px)
                    dy = abs(cy - py)

                    if dx > self.width / 2:
                        dx = self.width - dx
                    if dy > self.height / 2:
                        dy = self.height - dy

                    dist = (dx * dx + dy * dy) ** 0.5

                    if dist < min_distance:
                        conflict = True
                        break

                if not conflict:
                    valid_pos = True
                    best_x, best_y = cx, cy
                    break

            if valid_pos:
                placed_positions.append((best_x, best_y))

                self.image.blit(img, (best_x, best_y))

                if best_x + w > self.width:
                    self.image.blit(img, (best_x - self.width, best_y))

                if best_y + h > self.height:
                    self.image.blit(img, (best_x, best_y - self.height))

                if best_x + w > self.width and best_y + h > self.height:
                    self.image.blit(img, (best_x - self.width, best_y - self.height))
            else:
                DebugLogger.warn("Could not find valid position for an object")

        DebugLogger.init_sub("Decoration complete.")

    # ===========================================================
    # Update
    # ===========================================================

    def update(self, dt, player_pos=None, paused=False):
        """
        Update scroll position.

        Args:
            dt: Delta time in seconds
            player_pos: (x, y) player position for parallax
            paused: If True, skip auto-scroll accumulation
        """
        # Auto-scroll (skip if paused)
        if not paused:
            self.scroll_offset += self.scroll_speed * dt

        # Camera offset (always updates for parallax responsiveness)
        camera_x = 0
        camera_y = 0
        if player_pos:
            camera_x = (player_pos[0] - self.screen_width / 2) * self.parallax.x
            camera_y = -(player_pos[1] - self.screen_height / 2) * self.parallax.y

        # Combine scroll + camera, wrap to image dimensions
        final_x = (self.scroll_offset.x + camera_x) % self.width
        final_y = (self.scroll_offset.y + camera_y) % self.height

        self.render_offset_x = final_x
        self.render_offset_y = final_y

    # ===========================================================
    # Render
    # ===========================================================

    def render(self, surface):
        """
        Draw tiled background to surface.

        Args:
            surface: Target pygame surface
        """
        tiles_x = (self.screen_width // self.width) + 2
        tiles_y = (self.screen_height // self.height) + 2

        start_x = math.floor(-self.render_offset_x)
        start_y = math.floor(-self.render_offset_y)

        for tx in range(tiles_x):
            for ty in range(tiles_y):
                x = start_x + tx * self.width  # Clean integer math
                y = start_y + ty * self.height
                surface.blit(self.image, (x, y))


class BackgroundManager:
    """
    Manages multiple scrolling background layers.

    Provides:
    - Multi-layer support (back to front)
    - Runtime control (pause, speed, parallax)
    - Layer management (add, remove, clear)
    """

    __slots__ = ("screen_size", "layers", "_paused")

    def __init__(self, screen_size):
        """
        Initialize background manager.

        Args:
            screen_size: (width, height) tuple
        """
        self.screen_size = screen_size
        self.layers = []
        self._paused = False
        DebugLogger.init_entry("BackgroundManager")

    # ===========================================================
    # Layer Management
    # ===========================================================

    def add_layer(self, image_path, scroll_speed=(0, 30), parallax=(0.4, 0.6)):
        """
        Add a scrolling layer.

        Args:
            image_path: Path to background image
            scroll_speed: (x, y) scroll speed in px/sec
            parallax: (x, y) camera influence factor (0.0-1.0)
        """
        layer = BackgroundLayer(image_path, scroll_speed, parallax, self.screen_size)
        self.layers.append(layer)
        DebugLogger.init_sub(f"Added layer: speed={scroll_speed}, parallax={parallax}")

    def get_layer(self, index):
        """
        Get layer by index.

        Args:
            index: Layer index (0 = bottom/back)

        Returns:
            BackgroundLayer or None if out of range
        """
        if 0 <= index < len(self.layers):
            return self.layers[index]
        return None

    def remove_layer(self, index):
        """
        Remove layer by index.

        Args:
            index: Layer index to remove

        Returns:
            bool: True if removed, False if index out of range
        """
        if 0 <= index < len(self.layers):
            self.layers.pop(index)
            DebugLogger.action(f"Removed background layer {index}")
            return True
        return False

    def clear_layers(self):
        """Remove all layers."""
        self.layers.clear()
        DebugLogger.action("Cleared all background layers")

    @property
    def layer_count(self):
        """Get number of layers."""
        return len(self.layers)

    # ===========================================================
    # Runtime Controls
    # ===========================================================

    def set_scroll_speed(self, layer_index, speed):
        """
        Set scroll speed for a specific layer.

        Args:
            layer_index: Layer index (0 = bottom)
            speed: (x, y) tuple in pixels/second
        """
        layer = self.get_layer(layer_index)
        if layer:
            layer.scroll_speed = pygame.Vector2(speed)

    def set_parallax(self, layer_index, parallax):
        """
        Set parallax factor for a specific layer.

        Args:
            layer_index: Layer index (0 = bottom)
            parallax: (x, y) tuple (0.0 to 1.0)
        """
        layer = self.get_layer(layer_index)
        if layer:
            layer.parallax = pygame.Vector2(parallax)

    def set_all_scroll_speeds(self, speed):
        """
        Set scroll speed for all layers.

        Args:
            speed: (x, y) tuple in pixels/second
        """
        speed_vec = pygame.Vector2(speed)
        for layer in self.layers:
            layer.scroll_speed = speed_vec

    def pause(self):
        """Pause auto-scrolling (parallax still updates)."""
        self._paused = True

    def resume(self):
        """Resume auto-scrolling."""
        self._paused = False

    @property
    def paused(self):
        """Check if scrolling is paused."""
        return self._paused

    # ===========================================================
    # Update / Render
    # ===========================================================

    def update(self, dt, player_pos=None):
        """
        Update all layers.

        Args:
            dt: Delta time in seconds
            player_pos: (x, y) position for parallax calculation
        """
        for layer in self.layers:
            layer.update(dt, player_pos, paused=self._paused)

    def render(self, surface):
        """
        Render all layers bottom-up.

        Args:
            surface: Target pygame surface
        """
        for layer in self.layers:
            layer.render(surface)
