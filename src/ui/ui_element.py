"""
ui_element.py
-------------
Defines the abstract base class for all UI elements.
Every element (buttons, health bars, labels, etc.) inherits from this class
and implements its own behavior and rendering logic.

Responsibilities
----------------
- Define position, size, layer, visibility, and enable state.
- Provide interface methods for updating, handling clicks, and rendering.
- Implementing complex UI expression
"""
import pygame
from src.core.utils.debug_logger import DebugLogger

class UIElement:
    def __init__(self, x, y, width, height, layer=100):
        """
        Initialize a generic UI element.

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

    def update(self, mouse_pos):
        """
        Update element logic (hover effects, animations, etc.).

        Args:
            mouse_pos (tuple): Current mouse position.
        """
        pass

    def handle_click(self, mouse_pos):
        """
        Return an action string if clicked; otherwise None.

        Args:
            mouse_pos (tuple): Mouse click position.

        Returns:
            str | None: Action identifier or None if not clicked.
        """
        return None

    def update_value(self, **kwargs):
        """
            Updates the element's internal state based on provided data.
        """
        pass

    def render_surface(self):
        """
        Must be overridden in subclasses.
        Should return a pygame.Surface representing the element’s current state.

        Returns:
            pygame.Surface: Visual representation of the element.
        """
        DebugLogger.warn("Base render_surface() called directly")
        raise NotImplementedError

class BaseImage(UIElement):
    def __init__(self, x, y, image_path, layer=100):
        """
            Initializes the UI element with an image.

            This constructor attempts to load an image from the specified path,
            retrieves its dimensions, and then calls the parent class's
            initializer to set up the element's position, size, and layer.
            It includes error handling in case the image file fails to load.

            Args:
                x (int): The x-coordinate of the element.
                y (int): The y-coordinate of the element.
                image_path (str): The file path to the image to load.
                layer (int, optional): The rendering layer. Defaults to 100.
        """
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            width, height = self.image.get_size()
            DebugLogger.warn(f"Image load success: {image_path}")
        except pygame.error:
            DebugLogger.warn(f"Image load fail: {image_path}")

        super().__init__(x, y, width, height, layer)

    def render_surface(self):
        """
            Returns the surface of the loaded image for rendering.
        """
        return self.image

class ExpCheck(UIElement):
    def __init__(self, x, y, fill_image_path, current_key: str, max_key: str, layer=101):
        """
            Initializes a 'bar' style UI element (ex) HP, EXP bar).

            This element loads a "fill" image and is designed to be updated dynamically based on a current and maximum value.
            It prepares a separate surface for rendering the partial fill state.

            Args:
                x (int): The x-coordinate of the element.
                y (int): The y-coordinate of the element.
                fill_image_path (str): The file path to the "fill" image.
                current_key (str): The key used to retrieve the current value
                                   (ex) from a data dictionary in update_value.
                max_key (str): The key used to retrieve the maximum value.
                layer (int, optional): The rendering layer. Defaults to 101.
        """
        try:
            self.fill_image = pygame.image.load(fill_image_path).convert_alpha()
            width, height = self.fill_image.get_size()
        except pygame.error:
            DebugLogger.warn(f"ExpCheck load fail: {fill_image_path}")

        super().__init__(x, y, width, height, layer)

        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self.fill_width_max = width
        self.current_fill_area = pygame.Rect(0, 0, 0, height)

        self.value_key = current_key
        self.max_key = max_key

        self.current_value = 0
        self.max_value = 1

    def update_value(self, **kwargs):
        """
            Updates the fill state of the bar based on new data.

            This method uses the 'current_key' and 'max_key' (defined in __init__)
            to find and update the element's 'current_value' and 'max_value' from the provided keyword arguments.
            It then recalculates the fill percentage and updates the width of 'self.current_fill_area',
            which determines how much of the fill image is rendered.

            Args:
                **kwargs: Arbitrary keyword arguments (e.g., player_hp=50)
                          that may contain the new current and max values.
        """
        self.current_value = kwargs.get(self.value_key, self.current_value)
        self.max_value = kwargs.get(self.max_key, self.max_value)

        if self.max_value == 0:
            fill_percentage = 0
        else:
            fill_percentage = self.current_value / self.max_value

        current_clip_width = int(self.fill_width_max * fill_percentage)
        self.current_fill_area.width = current_clip_width

    def render_surface(self):
        """
            Renders the current state of the bar onto its internal surface.
        """
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(self.fill_image, (0, 0), area=self.current_fill_area)
        return self.surface

class GaugeNeedle(UIElement):
    def __init__(self, pivot_x, pivot_y, needle_image_path,
                 value_key: str, max_key: str,
                 min_angle=-80, max_angle=80, layer=102):
        """
            Initializes a rotating needle element for a gauge.

            This element loads a needle image and rotates it around a specified
            pivot point. The angle of rotation is determined by a current and
            maximum value, mapped between a min and max angle.

            Args:
                pivot_x (int): The x-coordinate of the rotation center (pivot).
                pivot_y (int): The y-coordinate of the rotation center (pivot).
                needle_image_path (str): The file path to the needle image.
                value_key (str): The key to retrieve the current value
                                 (e.g., from kwargs in update_value).
                max_key (str): The key to retrieve the maximum value.
                min_angle (int, optional): The angle (in degrees) corresponding
                                           to the minimum value. Defaults to -80.
                max_angle (int, optional): The angle (in degrees) corresponding
                                           to the maximum value. Defaults to 80.
                layer (int, optional): The rendering layer. Defaults to 102.
        """

        self.pivot = (pivot_x, pivot_y)
        try:
            self.original_needle_img = pygame.image.load(needle_image_path).convert_alpha()
        except pygame.error:
            DebugLogger.warn(f"GaugeNeedle load fail: {needle_image_path}")

        self.min_angle, self.max_angle = min_angle, max_angle

        self.value_key = value_key
        self.max_key = max_key

        self.current_value = 1
        self.max_value = 1

        self.current_angle = self.max_angle
        rotation_angle = -self.current_angle
        self.rotated_needle_img = pygame.transform.rotate(self.original_needle_img, rotation_angle)

        initial_rect = self.rotated_needle_img.get_rect(center=self.pivot)
        super().__init__(initial_rect.x, initial_rect.y, initial_rect.width, initial_rect.height, layer)

    def update_value(self, **kwargs):
        """
            Updates the needle's rotation based on new data.

            This method retrieves the current and max values from kwargs
            using the stored keys. It calculates the value percentage (0.0 to 1.0)
            and then interpolates this percentage to find the corresponding
            angle between 'min_angle' and 'max_angle'.

            Finally, it rotates the 'original_needle_img' to this new angle
            and updates the element's 'rect' to match the bounding box
            of the newly rotated image, centered on the pivot.

            Args:
                **kwargs: Arbitrary keyword arguments (e.g., player_speed=50)
                          that may contain the new current and max values.
        """
        self.current_value = kwargs.get(self.value_key, self.current_value)
        self.max_value = kwargs.get(self.max_key, self.max_value)

        val_percentage = self.current_value / self.max_value

        current_angle = self.min_angle + (val_percentage * (self.max_angle - self.min_angle))
        rotation_angle = -current_angle

        self.rotated_needle_img = pygame.transform.rotate(self.original_needle_img, rotation_angle)
        self.rect = self.rotated_needle_img.get_rect(center=self.pivot)

    def render_surface(self):
        """
            Returns the currently rotated needle image for rendering.
        """
        return self.rotated_needle_img