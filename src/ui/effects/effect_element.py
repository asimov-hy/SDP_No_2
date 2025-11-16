"""
effect_elements.py (Base Class)
-----------------
Defines the base structure and properties for all visual effect elements.

Responsibilities
----------------
- Maintain fundamental properties common to all effects (position, size, layer).
- Provide the standard interface (update, draw) that subclasses must implement.
- Manage visibility and enablement flags for runtime control.
"""
import pygame
from src.core.debug.debug_logger import DebugLogger

class EffectElements:
    """Base class for all transient visual effects and elements."""

    def __init__(self, x, y, width, height, layer=100):
        """
        Make EffectElements instance.

        Args:
            x (int): Top-left x position.
            y (int): Top-left y position.
            width (int): Element width in pixels.
            height (int): Element height in pixels.
            layer (int): Draw order; higher layers render on top.
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.layer = layer
        self.visible = True
        self.enabled = True

    def update(self):
        """
        Update element logic (effects)
        Base method that should be overridden by specific effect implementations.
        """
        pass


class ExplosionEffect(EffectElements):
    """
    Implements a time-limited visual effect characterized by scaling (shrinking) over its duration.
    """

    def __init__(self, x, y, image_path, layer=100):
        width, height = 0, 0
        self.effect_image = None
        self.is_active = False

        try:
            self.effect_image = pygame.image.load(image_path).convert_alpha()
            width, height = self.effect_image.get_size()
            DebugLogger.init(f"Image load success: {image_path}")
            self.position = (x, y)
            self.is_active = True
        except pygame.error:
            DebugLogger.warn(f"Image load fail: {image_path}")

        super().__init__(x, y, width, height, layer)

        self.duration = 0.3
        self.time_elapsed = 0.0
        self.current_size_factor = 1.0

    def update(self, add_time):
        """Updates the effect's timer and calculates the current size factor."""
        if not self.is_active or self.effect_image is None:
            return

        # Check for completion
        if self.time_elapsed >= self.duration:
            self.time_elapsed = self.duration
            self.is_active = False  # Mark for cleanup by EffectManager
            self.current_size_factor = 0.0
            return

        # Update timer and calculate linear scale factor (shrinking from 1.0 to 0.0)
        self.time_elapsed += add_time
        self.current_size_factor = 1.0 - self.time_elapsed / self.duration

        # Calculate new dimensions
        scale = self.current_size_factor
        current_width = int(self.effect_image.get_width() * scale)
        current_height = int(self.effect_image.get_height() * scale)

        # Update rect size while maintaining the center point
        if current_width > 0 and current_height > 0:
            current_rect = pygame.Rect(0, 0, current_width, current_height)
            current_rect.center = self.position  # Keep rect centered on original position
            self.rect = current_rect
        else:
            # Invalidate rect when size hits zero to avoid unexpected drawing issues
            self.rect.width = 0
            self.rect.height = 0

    def draw(self, draw_manager):
        if not self.is_active or self.effect_image is None:
            return

        real_width = self.rect.width
        real_height = self.rect.height

        if real_height > 0 and real_width > 0:
            scaled_image = pygame.transform.scale(self.effect_image, (real_width, real_height))
        else:
            return

        draw_manager.queue_draw(scaled_image, self.rect, self.layer)