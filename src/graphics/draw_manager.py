"""
draw_manager.py
---------------
Handles all rendering operations — batching draw calls, sorting layers,
and efficiently sending them to the main display surface.

Responsibilities
----------------
- Load and cache images used by entities_animation and ui.
- Maintain a draw queue (layered rendering system).
- Sort queued draw calls by layer each frame and render them.
- Provide helper methods for entities_animation and ui elements to queue themselves.
"""

import pygame
import math
import os
from src.core.debug.debug_logger import DebugLogger


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

        self.background = None  # Cached background surface (optional)

        self.debug_hitboxes = []  # Persistent list for queued hitboxes
        self.debug_obbs = []  # Persistent list for queued OBB lines
        self.debug_hitboxes = []  # Persistent list for queued hitboxes

        DebugLogger.init_entry("DrawManager")

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

        if scale != 1.0:
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
            # print(f"[DrawManager] SCALE: '{key}' → {img.get_size()} ({scale}x)")
            DebugLogger.state(f"Scaled '{key}' to {img.get_size()} ({scale:.2f}x)")

        self.images[key] = img

    def load_icon(self, name, size=(24, 24)):
        """
        Load or retrieve a cached ui icon.

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
        """
        Clear the draw queue before a new frame.

        Optimization:
        -------------
        Avoids recreating the dictionary every frame.
        Simply clears existing layer lists to reduce
        Python-level allocations and GC churn.
        """
        for layer_items in self.layers.values():
            layer_items.clear()

        if hasattr(self, "debug_hitboxes"):
            self.debug_hitboxes.clear()

        if hasattr(self, "debug_obbs"):
            self.debug_obbs.clear()

        self._layers_dirty = True

    def queue_draw(self, surface, rect, layer=0):
        """
        Add a drawable surface to the queue.

        Args:
            surface (pygame.Surface): The surface to draw.
            rect (pygame.Rect): The position rectangle.
            layer (int): Rendering layer (lower values draw first).
        """
        if surface is None or rect is None:
            DebugLogger.warn(f"Skipped invalid draw call at layer {layer}")
            return

        if layer not in self.layers:
            self.layers[layer] = []
            self._layers_dirty = True

        self.layers[layer].append((surface, rect))

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

    def queue_hitbox(self, rect, color=(255, 255, 0), width=1):
        """
        Queue a hitbox rectangle for rendering on the DEBUG layer.

        Optimization:
        -------------
        Avoids creating new Surfaces every frame by storing raw draw
        parameters instead of allocating `pygame.Surface` objects.
        These are drawn directly during render() for near-zero overhead.
        """
        if not hasattr(self, "debug_hitboxes"):
            self.debug_hitboxes = []

        # Store draw command for later rendering (no surface creation)
        self.debug_hitboxes.append((rect, color, width))

    def queue_obb(self, corners, color=(255, 0, 0), width=2):
        """
        Queue OBB corner lines for rendering on the DEBUG layer.

        Args:
            corners (list): List of (x, y) corner points
            color (tuple): RGB color for the lines
            width (int): Line width
        """
        if not hasattr(self, "debug_obbs"):
            self.debug_obbs = []

        # Store draw command for later rendering
        self.debug_obbs.append((corners, color, width))

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
    # Shape Prebaking (Optimization)
    # ===========================================================
    def prebake_shape(self, type: str, size: tuple[int, int] | int, color: tuple[int, int, int],
                      **kwargs) -> pygame.Surface:
        """
        Pre-render a shape into a reusable surface (optimization).

        INTERNAL USE ONLY: This method is called by BaseEntity.__init__()
        when shape_data is provided. Entities should NEVER call this directly.

        Entities: Use the shape_data pattern instead:
            # CORRECT usage:
            super().__init__(x, y,
                shape_data={"type": "circle", "size": (8, 8), "color": (255, 255, 0)},
                draw_manager=draw_manager
            )

            # INCORRECT usage (DO NOT DO THIS):
            image = draw_manager.prebake_shape("circle", (8, 8), (255, 255, 0))
            super().__init__(x, y, image=image)

        Returns:
            pygame.Surface: A surface with the shape pre-rendered
        """
        # Handle equilateral triangle size calculation
        if type == "triangle" and kwargs.get("equilateral"):
            w = size if isinstance(size, int) else size[0]
            h = int(w * math.sqrt(3) / 2)
            size = (w, h)

        # Create cache key for reusing identical shapes
        cache_key = f"shape_{type}_{size}_{color}_{tuple(sorted(kwargs.items()))}"

        # Return cached version if it exists
        if cache_key in self.images:
            return self.images[cache_key]

        # Square-pad shape to ensure correct rotation behavior
        max_dim = max(size)  # ensure square
        square_surface = pygame.Surface((max_dim, max_dim), pygame.SRCALPHA)

        # Find offsets to center the shape inside the square
        offset_x = (max_dim - size[0]) // 2
        offset_y = (max_dim - size[1]) // 2

        # Adjust rectangle to draw inside padded area
        temp_rect = pygame.Rect(offset_x, offset_y, size[0], size[1])

        # Draw shape onto *square* surface
        self._draw_shape(square_surface, type, temp_rect, color, **kwargs)

        # Cache and return
        self.images[cache_key] = square_surface
        return square_surface

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
        # -------------------------------------------------------
        # Background rendering (cached surface to avoid fill cost)
        # -------------------------------------------------------
        if hasattr(self, "background") and self.background is not None:
            target_surface.blit(self.background, (0, 0))
        else:
            target_surface.fill((50, 50, 100))  # fallback solid color

        # Cache sorted layer keys to avoid sorting every frame
        if self._layers_dirty:
            self._layer_keys_cache = sorted(self.layers.keys())
            self._layers_dirty = False

        # -------------------------------------------------------
        # Render each layer (surfaces + shapes)
        # -------------------------------------------------------
        for layer in self._layer_keys_cache:
            items = self.layers[layer]
            if not items:
                continue

            # Detect if layer contains shape commands
            shape_items = []
            surface_items = []
            for item in items:
                if isinstance(item[0], str):
                    shape_items.append(item)
                elif isinstance(item[0], pygame.Surface):
                    surface_items.append(item)

            # Batch blit all standard surfaces in one call
            if surface_items:
                target_surface.blits(surface_items)

            # Draw primitive shapes (rects, circles, etc.)
            for item in shape_items:
                _, shape_type, rect, color, kwargs = item
                self._draw_shape(target_surface, shape_type, rect, color, **kwargs)

        if debug:
            draw_count = sum(len(items) for items in self.layers.values())
            DebugLogger.state(f"Rendered {draw_count} queued surfaces and shapes", category="drawing")

        # -------------------------------------------------------
        # Optional debug overlay pass (hitboxes + OBBs)
        # -------------------------------------------------------
        if hasattr(self, "debug_hitboxes") and self.debug_hitboxes:
            """
            Directly draw debug hitboxes to avoid temporary surface allocation.
            Each tuple: (rect, color, width)
            """
            for rect, color, width in self.debug_hitboxes:
                pygame.draw.rect(target_surface, color, rect, width)

        if hasattr(self, "debug_obbs") and self.debug_obbs:
            """
            Draw OBB corner lines for rotated hitboxes.
            Each tuple: (corners, color, width)
            """
            for corners, color, width in self.debug_obbs:
                pygame.draw.lines(target_surface, color, True, corners, width)

    # ===========================================================
    # Shape Rendering Helper
    # ===========================================================
    def _draw_shape(self, surface: pygame.Surface, shape_type: str,
                    rect: pygame.Rect, color: tuple[int, int, int], **kwargs) -> None:
        """
        Internal helper for drawing primitive shapes on a surface.

        Args:
            surface: Target surface to draw onto
            shape_type: "rect", "circle", "triangle", "polygon", etc.
            rect: Shape bounds
            color: RGB color
            **kwargs: Shape-specific parameters
        """
        width = kwargs.get("width", 0)

        # Calculate points for polygon-based shapes
        points = self._calculate_shape_points(shape_type, rect.width, rect.height, **kwargs)

        if points:
            # All polygon-based shapes (triangle, polygon, future shapes)
            pygame.draw.polygon(surface, color, points, width)

            # For DEBUG
            # if shape_type == "triangle" and len(points) > 0:
            #     tip = points[0]  # First point is the tip for "up" triangles
            #     pygame.draw.circle(surface, (255, 255, 0), tip, 3)
        elif shape_type == "rect":
            pygame.draw.rect(surface, color, rect, width)
        elif shape_type == "circle":
            pygame.draw.circle(surface, color, rect.center, rect.width // 2, width)
        elif shape_type == "ellipse":
            pygame.draw.ellipse(surface, color, rect, width)
        elif shape_type == "line":
            start = kwargs.get("start_pos")
            end = kwargs.get("end_pos")
            if start and end:
                pygame.draw.line(surface, color, start, end, width)
        else:
            DebugLogger.warn(f"Unknown shape type: {shape_type}")

    def _calculate_shape_points(self, shape_type, w, h, **kwargs):
        """
        Centralized point calculation for all geometric shapes.
        Returns None for shapes that don't use points (rect, circle, ellipse).

        Args:
            shape_type: "triangle", "polygon", etc.
            w, h: Shape dimensions
            **kwargs: Shape-specific params (pointing, points, etc.)

        Returns:
            list | None: Vertex points or None for non-polygon shapes
        """
        if shape_type == "triangle":
            pointing = kwargs.get("pointing", "up")
            if pointing == "up":
                return [(w // 2, 0), (0, h), (w, h)]
            elif pointing == "down":
                return [(w // 2, h), (0, 0), (w, 0)]
            elif pointing == "left":
                return [(0, h // 2), (w, 0), (w, h)]
            elif pointing == "right":
                return [(w, h // 2), (0, 0), (0, h)]
            else:
                DebugLogger.warn(f"Invalid triangle direction '{pointing}', defaulting to 'up'")
                return [(w // 2, 0), (0, h), (w, h)]

        elif shape_type == "polygon":
            # Custom points passed directly
            return kwargs.get("points", [])

        # Future shapes: hexagon, star, arrow, etc. go here

        return None  # Non-polygon shapes (rect, circle, ellipse)

