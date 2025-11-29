"""
draw_manager.py
---------------
Centralized rendering manager for batching and layered draw calls.

Responsibilities:
- Load and cache images
- Maintain layered draw queue
- Render queued surfaces and shapes
- Debug overlay rendering
"""

import math
import os

import pygame

from src.core.debug.debug_logger import DebugLogger


class DrawManager:
    """Handles all rendering operations with layered batching."""

    # ===========================================================
    # Initialization
    # ===========================================================

    def __init__(self):
        """Initialize draw manager with empty queues."""
        # Image cache
        self.images = {}

        # Layer queues
        self.surface_layers = {}  # {layer: [(surface, rect), ...]}
        self.shape_layers = {}    # {layer: [shape_data, ...]}
        self._layer_keys_cache = []
        self._layers_dirty = False

        # Background (reference only, not owned)
        self.background = None
        self.bg_manager = None
        self._bg_cache = None

        # Debug overlays
        self.debug_hitboxes = []
        self.debug_obbs = []

        # Screen shake
        self.shake_offset = (0, 0)
        self.shake_timer = 0.0
        self.shake_intensity = 0.0
        self.shake_duration = 0.0

        DebugLogger.init_entry("DrawManager")

    # ===========================================================
    # Image Loading
    # ===========================================================

    def load_image(self, key, path, scale=1.0):
        """
        Load and cache an image.

        Args:
            key: Cache identifier
            path: File path to image
            scale: Scaling factor (default 1.0)
        """
        try:
            img = pygame.image.load(path).convert_alpha()
        except FileNotFoundError:
            DebugLogger.warn(f"Missing image at {path}")
            img = pygame.Surface((40, 40))
            img.fill((255, 255, 255))

        if scale != 1.0:
            w, h = img.get_size()
            img = pygame.transform.scale(img, (int(w * scale), int(h * scale)))
            DebugLogger.state(f"Scaled '{key}' to {img.get_size()} ({scale:.2f}x)")

        self.images[key] = img

    def load_icon(self, name, size=(24, 24)):
        """
        Load or retrieve a cached icon.

        Args:
            name: Icon filename (without extension)
            size: Target size tuple

        Returns:
            pygame.Surface: Icon surface
        """
        key = f"icon_{name}_{size[0]}x{size[1]}"
        if key in self.images:
            return self.images[key]

        path = os.path.join("assets", "images", "icons", f"{name}.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, size)
            DebugLogger.action(f"Loaded icon '{name}' ({size[0]}x{size[1]})")
        except FileNotFoundError:
            img = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(img, (255, 255, 255), img.get_rect(), 1)
            DebugLogger.warn(f"Missing icon '{name}' at {path}")

        self.images[key] = img
        return self.images[key]

    def get_image(self, key):
        """
        Retrieve cached image by key.

        Args:
            key: Cache identifier

        Returns:
            pygame.Surface or None
        """
        img = self.images.get(key)
        if img is None:
            DebugLogger.warn(f"No cached image for key '{key}'")
        return img

    def get_entity_image(self, entity_type, size=None, config=None, color=None, image_path=None):
        """
        Get entity image with automatic loading/generation.

        Args:
            entity_type: Identifier string
            size: Target size tuple
            config: Optional config dict with image/size/color/scale
            color: Color for shape-based entities
            image_path: Direct path (overrides config)

        Returns:
            pygame.Surface: Always returns valid image
        """
        # Parse config
        if config:
            image_path = image_path or config.get("image")
            size = size or config.get("size", (32, 32))
            color = color or config.get("color")
            scale = config.get("scale", 1.0)
        else:
            size = size or (32, 32)
            scale = 1.0

        # Cache key
        cache_key = (entity_type, size[0], size[1])
        if color:
            cache_key = (entity_type, size[0], size[1], tuple(color))

        if cache_key in self.images:
            return self.images[cache_key]

        # Try loading from path
        if image_path:
            try:
                img = pygame.image.load(image_path).convert_alpha()
                if scale != 1.0:
                    new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
                    img = pygame.transform.scale(img, new_size)
                else:
                    img = pygame.transform.scale(img, size)
                self.images[cache_key] = img
                DebugLogger.action(f"Loaded entity image: {entity_type} from {image_path}")
                return img
            except Exception as e:
                DebugLogger.warn(f"Failed to load {image_path}: {e}, using fallback")

        # Try color fill
        if color:
            img = pygame.Surface(size, pygame.SRCALPHA)
            img.fill(color)
            self.images[cache_key] = img
            return img

        # Fallback
        DebugLogger.warn(f"No image/color for {entity_type}, using fallback placeholder")
        img = self._generate_fallback(size, entity_type)
        self.images[cache_key] = img
        return img

    # ===========================================================
    # Queue Management
    # ===========================================================

    def clear(self):
        """Clear all draw queues for new frame."""
        for layer_items in self.surface_layers.values():
            layer_items.clear()
        for layer_items in self.shape_layers.values():
            layer_items.clear()
        self.debug_hitboxes.clear()
        self.debug_obbs.clear()

    def trigger_shake(self, intensity=8.0, duration=0.3):
        """Start screen shake effect."""
        self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_timer = duration

    def update_shake(self, dt):
        """Update screen shake (call each frame)."""
        if self.shake_timer > 0:
            self.shake_timer -= dt
            t = self.shake_timer / self.shake_duration if self.shake_duration > 0 else 0
            import math
            self.shake_offset = (
                int(math.sin(self.shake_timer * 50) * self.shake_intensity * t),
                int(math.cos(self.shake_timer * 40) * self.shake_intensity * t)
            )
        else:
            self.shake_offset = (0, 0)

    def queue_draw(self, surface, rect, layer=0):
        """
        Queue a surface for drawing.

        Args:
            surface: pygame.Surface to draw
            rect: Position rectangle
            layer: Render layer (lower = first)
        """
        if surface is None or rect is None:
            DebugLogger.warn(f"Skipped invalid draw call at layer {layer}")
            return

        if layer not in self.surface_layers:
            self.surface_layers[layer] = []
            self._layers_dirty = True

        self.surface_layers[layer].append((surface, rect))

    def draw_entity(self, entity, layer=0):
        """
        Queue entity with image and rect attributes.

        Args:
            entity: Object with .image and .rect
            layer: Render layer
        """
        if hasattr(entity, "image") and hasattr(entity, "rect"):
            self.queue_draw(entity.image, entity.rect, layer)
        else:
            DebugLogger.warn(f"Invalid entity: {entity} (missing image/rect)")

    def queue_shape(self, shape_type, rect, color, layer=0, **kwargs):
        """
        Queue a primitive shape.

        Args:
            shape_type: "rect", "circle", "polygon", etc.
            rect: Position and dimensions
            color: RGB tuple
            layer: Render layer
            **kwargs: Shape-specific params
        """
        if layer not in self.shape_layers:
            self.shape_layers[layer] = []
            self._layers_dirty = True

        self.shape_layers[layer].append((shape_type, rect, color, kwargs))

    def queue_hitbox(self, rect, color=(255, 255, 0), width=1):
        """Queue debug hitbox rectangle."""
        self.debug_hitboxes.append((rect, color, width))

    def queue_obb(self, corners, color=(255, 0, 0), width=2):
        """Queue debug OBB lines."""
        self.debug_obbs.append((corners, color, width))

    # ===========================================================
    # Shape Helpers
    # ===========================================================

    def prebake_shape(self, shape_type, size, color, **kwargs):
        """
        Pre-render shape into reusable surface.

        Internal use by BaseEntity. Use shape_data pattern instead.

        Args:
            shape_type: Shape type string
            size: Tuple or int
            color: RGB tuple
            **kwargs: Shape params

        Returns:
            pygame.Surface: Pre-rendered shape
        """
        # Handle equilateral triangle
        if shape_type == "triangle" and kwargs.get("equilateral"):
            w = size if isinstance(size, int) else size[0]
            h = int(w * math.sqrt(3) / 2)
            size = (w, h)

        cache_key = f"shape_{shape_type}_{size}_{color}_{tuple(sorted(kwargs.items()))}"
        if cache_key in self.images:
            return self.images[cache_key]

        # Square-pad for rotation
        max_dim = max(size)
        square_surface = pygame.Surface((max_dim, max_dim), pygame.SRCALPHA)

        offset_x = (max_dim - size[0]) // 2
        offset_y = (max_dim - size[1]) // 2
        temp_rect = pygame.Rect(offset_x, offset_y, size[0], size[1])

        self._draw_shape(square_surface, shape_type, temp_rect, color, **kwargs)

        self.images[cache_key] = square_surface
        return square_surface

    def _calculate_shape_points(self, shape_type, w, h, **kwargs):
        """
        Calculate vertex points for polygon shapes.

        Returns:
            list or None: Points for polygon shapes, None for others
        """
        if shape_type == "triangle":
            pointing = kwargs.get("pointing", "up")
            directions = {
                "up": [(w // 2, 0), (0, h), (w, h)],
                "down": [(w // 2, h), (0, 0), (w, 0)],
                "left": [(0, h // 2), (w, 0), (w, h)],
                "right": [(w, h // 2), (0, 0), (0, h)]
            }
            if pointing not in directions:
                DebugLogger.warn(f"Invalid triangle direction '{pointing}', defaulting to 'up'")
                pointing = "up"
            return directions[pointing]

        elif shape_type == "polygon":
            return kwargs.get("points", [])

        return None

    def _draw_shape(self, surface, shape_type, rect, color, **kwargs):
        """
        Draw primitive shape on surface.

        Args:
            surface: Target surface
            shape_type: Shape type string
            rect: Shape bounds
            color: RGB tuple
            **kwargs: Shape params
        """
        width = kwargs.get("width", 0)
        points = self._calculate_shape_points(shape_type, rect.width, rect.height, **kwargs)

        if points:
            pygame.draw.polygon(surface, color, points, width)
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

    # ===========================================================
    # Rendering
    # ===========================================================

    def render(self, target_surface, debug=False):
        """
        Render all queued items to target surface.

        Args:
            target_surface: Main display surface
            debug: Log render stats if True
        """
        self.surface = target_surface

        # Background
        self._render_background(target_surface)

        # Update layer cache
        if self._layers_dirty:
            all_layers = set(self.surface_layers.keys()) | set(self.shape_layers.keys())
            self._layer_keys_cache = sorted(all_layers)
            self._layers_dirty = False

        # Render layers
        for layer in self._layer_keys_cache:
            if layer in self.surface_layers and self.surface_layers[layer]:
                if self.shake_offset != (0, 0):
                    shifted = [(surf, rect.move(self.shake_offset)) for surf, rect in self.surface_layers[layer]]
                    target_surface.blits(shifted)
                else:
                    target_surface.blits(self.surface_layers[layer])

            if layer in self.shape_layers:
                for shape_type, rect, color, kwargs in self.shape_layers[layer]:
                    self._draw_shape(target_surface, shape_type, rect, color, **kwargs)

        # Debug overlays
        self._render_debug(target_surface)

        if debug:
            surface_count = sum(len(items) for items in self.surface_layers.values())
            shape_count = sum(len(items) for items in self.shape_layers.values())
            DebugLogger.state(f"Rendered {surface_count} surfaces and {shape_count} shapes", category="drawing")

    def _render_background(self, target_surface):
        """Render background (scrolling, static, or fallback)."""
        if self.bg_manager is not None:
            self.bg_manager.render(target_surface)
        elif self.background is not None:
            target_surface.blit(self.background, (0, 0))
        else:
            if self._bg_cache is None:
                self._bg_cache = pygame.Surface(target_surface.get_size())
                self._bg_cache.fill((50, 50, 100))
            target_surface.blit(self._bg_cache, (0, 0))

    def _render_debug(self, target_surface):
        """Render debug hitboxes and OBBs."""
        for rect, color, width in self.debug_hitboxes:
            pygame.draw.rect(target_surface, color, rect, width)

        for corners, color, width in self.debug_obbs:
            pygame.draw.lines(target_surface, color, True, corners, width)

    # ===========================================================
    # Fallback
    # ===========================================================

    def _generate_fallback(self, size, entity_type="unknown"):
        """
        Generate placeholder image.

        Args:
            size: Tuple (width, height)
            entity_type: For debug purposes

        Returns:
            pygame.Surface: Magenta placeholder
        """
        fallback_path = "assets/images/null.png"

        if os.path.exists(fallback_path):
            try:
                img = pygame.image.load(fallback_path).convert_alpha()
                return pygame.transform.scale(img, size)
            except Exception as e:
                DebugLogger.warn(f"Failed to load fallback {fallback_path}: {e}")

        img = pygame.Surface(size, pygame.SRCALPHA)
        img.fill((255, 0, 255))
        pygame.draw.rect(img, (255, 255, 255), img.get_rect(), 2)

        if size[0] >= 16 and size[1] >= 16:
            font = pygame.font.Font(None, min(size[0], 24))
            text = font.render("?", True, (255, 255, 255))
            text_rect = text.get_rect(center=(size[0] // 2, size[1] // 2))
            img.blit(text, text_rect)

        return img