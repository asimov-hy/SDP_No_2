"""
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
from src.core.game_settings import Layers


class DrawManager:
    """Centralized rendering manager that handles all draw operations."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self):
        self.images = {}
        # Layer buckets instead of flat queue
        self.layers = {}  # {layer: [(surface, rect), ...]}
        self._layer_keys_cache = []
        self._layers_dirty = False
        self.surface = None  # Expose active surface for debug/hitbox draws
        DebugLogger.init("║{:<59}║".format(f"\t[DrawManager][INIT]\t\t→ Initialized"), show_meta=False)

    # --------------------------------------------------------
    # Image Loading
    # --------------------------------------------------------
    def load_image(self, key, path, scale=1.0):
        """
        Load an image from file and store it in the cache.

        Args:
            key (str): Identifier used to retrieve this image later.
            path (str): File path to the image asset.
            scale (float): Optional scaling factor to resize the image.
        """
        try:
            img = pygame.image.load(path).convert_alpha()
            # DebugLogger.action(f"Loaded image '{key}' from {path}")

        except FileNotFoundError:
            DebugLogger.warn(f"Missing image at {path}")
            img = pygame.Surface((40, 40))
            img.fill((255, 255, 255))
            DebugLogger.warn(f"Missing image: {path}")

        if scale != 1.0:
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
            # print(f"[DrawManager] SCALE: '{key}' → {img.get_size()} ({scale}x)")
            DebugLogger.state(f"Scaled '{key}' to {img.get_size()} ({scale:.2f}x)")

        self.images[key] = img

    def load_icon(self, name, size=(24, 24)):
        """
        Load or retrieve a cached UI icon.

        Args:
            name (str): Name of the icon file (without extension).
            size (tuple[int, int]): Target icon size in pixels.

        Returns:
            pygame.Surface: The loaded or cached icon surface.
        """
        key = f"icon_{name}_{size[0]}x{size[1]}"
        if key in self.images:
            return self.images[key]

        path = os.path.join("assets", "images", "icons", f"{name}.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            self.images[key] = img
            DebugLogger.action(f"Loaded icon '{name}' ({size[0]}x{size[1]})")

        except FileNotFoundError:
            img = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(img, (255, 255, 255), img.get_rect(), 1)
            self.images[key] = img
            DebugLogger.warn(f"Missing icon '{name}' at {path}")

        return self.images[key]

    def get_image(self, key):
        """
        Retrieve a previously loaded image by key.

        Args:
            key (str): Identifier used when loading the image.

        Returns:
            pygame.Surface | None: The corresponding image or None if missing.
        """
        img = self.images.get(key)
        if img is None:
            DebugLogger.warn(f"No cached image for key '{key}'")
        return img

    # ===========================================================
    # Draw Queue Management
    # ===========================================================
    def clear(self):
        """Clear the draw queue before a new frame."""
        self.layers.clear()
        self._layers_dirty = True

    def queue_draw(self, surface, rect, layer=0):
        """
        Add a drawable surface to the queue.

        Args:
            surface (pygame.Surface): The surface to draw.
            rect (pygame.Rect): The position rectangle.
            layer (int): Rendering layer (lower values draw first).
        """
        if layer not in self.layers:
            self.layers[layer] = []
            self._layers_dirty = True
        self.layers[layer].append((surface, rect))

        if surface is None or rect is None:
            DebugLogger.warn(f"Skipped invalid draw call at layer {layer}")
            return

    def draw_entity(self, entity, layer=0):
        """
        Queue an entity that contains an image and rect.

        Args:
            entity: Object with `.image` and `.rect` attributes.
            layer (int): Rendering layer.
        """
        if hasattr(entity, "image") and hasattr(entity, "rect"):
            self.queue_draw(entity.image, entity.rect, layer)
        else:
            DebugLogger.warn(f"Invalid entity: {entity} (missing image/rect)")

    def queue_hitbox(self, rect, color=(255, 255, 0), width = 1):
        """Queue a hitbox rectangle for rendering on the DEBUG layer."""
        surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(surf, color, surf.get_rect(), width)
        self.queue_draw(surf, rect, layer=Layers.DEBUG)  # Layers.DEBUG

    # ===========================================================
    # Shape Queueing
    # ===========================================================
    def queue_shape(self, shape_type, rect, color, layer=0, **kwargs):
        """
        Queue a primitive shape to be drawn on the specified layer.

        Args:
            shape_type (str): Type of shape ("rect", "circle", "polygon", etc.).
            rect (pygame.Rect): Position and dimensions of the shape.
            color (tuple[int, int, int]): RGB color of the shape.
            layer (int): Rendering layer (lower values draw first).
            **kwargs: Additional shape-specific parameters (e.g., width, points).
        """
        if layer not in self.layers:
            self.layers[layer] = []
            self._layers_dirty = True

        # Add tagged shape command for later rendering
        self.layers[layer].append(("shape", shape_type, rect, color, kwargs))

    # ===========================================================
    # Rendering
    # ===========================================================
    def render(self, target_surface, debug=False):
        """
        Render all queued surfaces to the given target surface.

        Args:
            target_surface (pygame.Surface): The main display or game surface.
            debug (bool): If True, logs the number of items rendered.
        """
        self.surface = target_surface
        target_surface.fill((50, 50, 100))  # Background color

        # Cache sorted layer keys to avoid sorting every frame
        if self._layers_dirty:
            self._layer_keys_cache = sorted(self.layers.keys())
            self._layers_dirty = False


        # -------------------------------------------------------
        # Render each layer (surfaces + shapes)
        # -------------------------------------------------------
        for layer in self._layer_keys_cache:
            for item in self.layers[layer]:
                # Handle traditional surface blit
                if isinstance(item[0], pygame.Surface):
                    surface, rect = item
                    blit_pos = (round(rect.centerx - surface.get_width() / 2),
                                round(rect.centery - surface.get_height() / 2))
                    target_surface.blit(surface, blit_pos)

                # Handle shape draw command
                elif isinstance(item[0], str) and item[0] == "shape":
                    _, shape_type, rect, color, kwargs = item
                    self._draw_shape(target_surface, shape_type, rect, color, **kwargs)

        if debug:
            draw_count = sum(len(items) for items in self.layers.values())
            DebugLogger.state(f"Rendered {draw_count} queued surfaces and shapes")

        # -------------------------------------------------------
        # Optional debug overlay pass (hitboxes)
        # -------------------------------------------------------
        if debug and hasattr(self, "debug_hitboxes"):
            for hb in self.debug_hitboxes:
                hb.draw_debug(target_surface)

    # ===========================================================
    # Shape Rendering Helper
    # ===========================================================
    def _draw_shape(self, surface, shape_type, rect, color, **kwargs):
        """
        Internal helper for drawing primitive shapes on a surface.

        Args:
            surface (pygame.Surface): Target surface to draw onto.
            shape_type (str): Type of shape ("rect", "circle", "ellipse", etc.).
            rect (pygame.Rect): Shape bounds.
            color (tuple[int, int, int]): RGB color.
            **kwargs: Optional keyword args (e.g., width, points, start_pos, end_pos).
        """
        width = kwargs.get("width", 0)

        if shape_type == "rect":
            pygame.draw.rect(surface, color, rect, width)
        elif shape_type == "circle":
            pygame.draw.circle(surface, color, rect.center, rect.width // 2, width)
        elif shape_type == "ellipse":
            pygame.draw.ellipse(surface, color, rect, width)
        elif shape_type == "polygon":
            points = kwargs.get("points", [])
            if points:
                pygame.draw.polygon(surface, color, points, width)
        elif shape_type == "line":
            start = kwargs.get("start_pos")
            end = kwargs.get("end_pos")
            if start and end:
                pygame.draw.line(surface, color, start, end, width)
        else:
            DebugLogger.warn(f"Unknown shape type: {shape_type}")
