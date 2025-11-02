"""
NOTE: This module is theoretical and can be modified freely.

draw_manager.py
---------------
Handles all rendering operations — batching draw calls, sorting layers,
and efficiently sending them to the main display surface.

Responsibilities
----------------
- Load and cache images used by entities and UI.
- Maintain a draw queue (layered rendering system).
- Sort queued draw calls by layer each frame and render them.
- Provide helper methods for entities and UI elements to queue themselves.
"""

import pygame
import os
from src.core.utils.debug_logger import DebugLogger

class DrawManager:
    """Centralized rendering manager that handles all draw operations."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self):
        self.images = {}          # Cached loaded images
        self.draw_queue = []      # (layer, surface, rect)
        DebugLogger.system("DrawManager", "Initialized draw system")

    # --------------------------------------------------------
    # Image Loading
    # --------------------------------------------------------
    def load_image(self, key, path, scale=1.0):
        """
        Load an image from file and store it under a given key.
        """
        try:
            img = pygame.image.load(path).convert_alpha()
            # DebugLogger.action("DrawManager", f"Loaded image '{key}' from {path}")

        except FileNotFoundError:
            print(f"[DrawManager] WARN: Missing image at {path}")
            img = pygame.Surface((40, 40))
            img.fill((255, 255, 255))
            DebugLogger.warn("DrawManager", f"Missing image: {path}")

        if scale != 1.0:
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
            print(f"[DrawManager] SCALE: '{key}' → {img.get_size()} ({scale}x)")
            DebugLogger.state("DrawManager", f"Scaled '{key}' to {img.get_size()} ({scale:.2f}x)")

        self.images[key] = img

    def load_icon(self, name, size=(24, 24)):
        """
        Load or retrieve a cached UI icon.
        Icons should be stored in 'assets/images/icons/'.
        Automatically caches icons based on name and size.
        """
        key = f"icon_{name}_{size[0]}x{size[1]}"
        if key in self.images:
            return self.images[key]

        path = os.path.join("assets", "images", "icons", f"{name}.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, size)
            self.images[key] = img
            DebugLogger.action("DrawManager", f"Loaded icon '{name}' ({size[0]}x{size[1]})")

        except FileNotFoundError:
            img = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(img, (255, 255, 255), img.get_rect(), 1)
            self.images[key] = img
            DebugLogger.warn("DrawManager", f"Missing icon '{name}' at {path}")

        return self.images[key]

    def get_image(self, key):
        """Retrieve a previously loaded image."""
        img = self.images.get(key)
        if img is None:
            DebugLogger.warn("DrawManager", f"No cached image for key '{key}'")
        return img

    # ===========================================================
    # Draw Queue Management
    # ===========================================================
    def clear(self):
        """Clear the draw queue before a new frame."""
        self.draw_queue.clear()

    def queue_draw(self, surface, rect, layer=0):
        """Add a drawable surface to the draw queue."""
        self.draw_queue.append((layer, surface, rect))

    def draw_entity(self, entity, layer=0):
        """Queue an entity (must have .image and .rect)."""
        if hasattr(entity, "image") and hasattr(entity, "rect"):
            self.queue_draw(entity.image, entity.rect, layer)
        else:
            DebugLogger.warn("DrawManager", f"Invalid entity: {entity} (missing image/rect)")

    # ===========================================================
    # Rendering
    # ===========================================================
    def render(self, target_surface, debug=False):
        """
        Render all queued surfaces to the given target surface.

        Args:
            target_surface (pygame.Surface): Main game surface or display.
            debug (bool): If True, print how many items were rendered.
        """
        target_surface.fill((50, 50, 100))  # Background color

        for layer, image, rect in sorted(self.draw_queue, key=lambda x: x[0]):
            target_surface.blit(image, rect)

        if debug:
            DebugLogger.state("DrawManager", f"Rendered {len(self.draw_queue)} queued surfaces")
