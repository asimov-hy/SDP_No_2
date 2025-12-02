"""
needle.py
---------
UI element that rotates based on bound data.
Useful for gauges, speedometers, or clock-like interfaces.
"""
# Use Gemini for comment

import pygame
from typing import Tuple

from ..core.ui_element import UIElement
from ..core.ui_loader import register_element


@register_element("needle")
class UINeedle(UIElement):
    """
    A UI element that visualizes a value by rotating an image.
    Supports dynamic data binding for both current and max values.
    """

    def __init__(self, config):
        """
        Initialize the needle element.

        Args:
            config: Configuration dictionary loaded from YAML.
        """
        super().__init__(config)

        # Retrieve data configuration
        # Fallback to 'config' if 'data' key is missing (supports Flat Format YAML)
        data = config.get("data")
        if data is None:
            data = config

        # Binding path for dynamic max value (e.g., 'player.max_health')
        self.bind_max_path = data.get("bind_max")

        # Value range settings
        self.min_value = data.get("min_value", 0)  # Health typically starts at 0

        # Max value: use config default, will be overridden by bind_max if set
        self.max_value = data.get("max_value", 100)

        # Binding path for current value (e.g., 'player.health')
        self.bind_path = data.get("bind")

        # Initial current value - will be updated by binding system
        self.current_value = data.get("current_value", self.max_value)

        # Angle settings in degrees
        # Typically negative for left, positive for right (e.g., -60 to 60)
        self.min_angle = data.get("min_angle", -80)
        self.max_angle = data.get("max_angle", 80)

        # Calculate initial rotation
        self._update_rotation()

    def update(self, dt: float, mouse_pos: Tuple[int, int], binding_system=None):
        """
        Update the needle state every frame.
        """
        # 1. Update standard bindings (updates self.current_value automatically via parent)
        super().update(dt, mouse_pos, binding_system)

        # 2. Update dynamic max value if a binding path exists
        # This allows the gauge to adjust if the player's max stats change (e.g., Level Up)
        if binding_system and self.bind_max_path:
            new_max = binding_system.resolve(self.bind_max_path)
            if new_max is not None:
                self.max_value = float(new_max)

        # 3. Recalculate rotation based on new values
        self._update_rotation()

    def _update_rotation(self):
        """
        Calculates the rotation angle based on current_value, min_value, and max_value.
        """
        # Prevent division by zero if range is invalid
        value_range = self.max_value - self.min_value
        if value_range <= 0:
            return

        # Calculate the normalized ratio (0.0 to 1.0)
        # Example: If val=1, min=1, max=3 -> (1-1)/2 = 0.0 (0%)
        normalized_val = self.current_value - self.min_value
        ratio = normalized_val / value_range

        # Clamp the ratio to ensure the needle doesn't rotate beyond limits
        ratio = max(0.0, min(1.0, ratio))

        # Linear Interpolation (Lerp) to find the target angle
        target_angle = self.min_angle + (self.max_angle - self.min_angle) * ratio

        # Optimization: Only mark dirty (re-render) if the angle changed significantly
        current_rot = getattr(self, "rotation", None)
        if current_rot is None or abs(current_rot - target_angle) > 0.01:
            self.rotation = target_angle
            self.mark_dirty()

    def _build_surface(self) -> pygame.Surface:
        """
        Render the rotated needle image onto a surface.
        """
        image = self._load_image()

        # Create a transparent surface matching the element size
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        if image:
            # Pygame's rotation is counter-clockwise (positive moves left).
            # We negate it so positive values move clockwise (right).
            final_angle = -self.rotation

            # Rotate the image
            rotated_image = pygame.transform.rotate(image, final_angle)

            # Center the rotated image within the element's bounding box
            # This simulates rotating around a center pivot
            local_center = (self.width // 2, self.height // 2)
            new_rect = rotated_image.get_rect(center=local_center)

            # Draw to surface
            surf.blit(rotated_image, new_rect)

        return surf
