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
from src.core.utils.debug_logger import DebugLogger


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

    Responsibilities
    - Load the specific explosion sprite image.
    - Manage the effect's duration, elapsed time, and active status.
    - Implement size scaling logic based on elapsed time (shrinking effect).
    - Dynamically resize and center the sprite image during the draw cycle.
    """

    def __init__(self, x, y, image_path, layer=100):
        width, height = 0, 0
        try:
            # Load the sprite image for the explosion
            self.effect_image = pygame.image.load(image_path).convert_alpha()
            width, height = self.effect_image.get_size()
            DebugLogger.init(f"Image load success: {image_path}")
            # Store the original center position
            self.position = (x, y)
        except pygame.error:
            DebugLogger.warn(f"Image load fail: {image_path}")

        # Initialize base properties (rect, layer)
        super().__init__(x, y, width, height, layer)

        self.duration = 0.3  # 효과 지속 시간 (초)
        self.time_elapsed = 0.0
        self.is_active = True  # Flag indicating if the effect is currently running
        self.current_size_factor = 1.0  # Current scaling factor (1.0 = full size)

    def update(self, add_time):
        """
        Updates the effect's timer and calculates the current size factor.

        Args:
            add_time (float): Delta time (dt) since the last frame.
        """
        if not self.is_active:
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

    def draw(self, surface):
        """
        Scales the image based on the current size factor and draws it to the surface.

        Args:
            surface (pygame.Surface): The target surface to draw onto.
        """
        if not self.is_active:
            return

        real_width = self.rect.width
        real_height = self.rect.height

        # Scale the image only if dimensions are valid
        if real_height > 0 and real_width > 0:
            scaled_image = pygame.transform.scale(self.effect_image, (real_width, real_height))
        else:
            return

        # Blit the scaled image using the updated, centered rect
        surface.blit(scaled_image, self.rect)
