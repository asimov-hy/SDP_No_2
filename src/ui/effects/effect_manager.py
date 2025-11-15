"""
effect_manager.py
-----------------
Manages all transient visual effects (explosions, particles) in the game.

Responsibilities
----------------
- Implement the Singleton pattern to ensure only one instance exists.
- Initialize and store paths to all defined effect sprites.
- Update all active effects each frame, advancing their animation and duration.
- Clean up effects that have finished their lifecycle.
- Provide a centralized method (create_explosion) for generating new effects.
"""
from src.ui.effects.effect_element import *
from src.core.utils.debug_logger import DebugLogger
import random


class EffectManager:
    """Manages the creation, updating, and drawing of all in-game visual effects."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensures only a single instance of EffectManager exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # -----------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------
    def __init__(self, screen_width, screen_height):
        """
        Initializes the effect manager. Executed only once due to Singleton design.

        Args:
            screen_width (int): The width of the game display.
            screen_height (int): The height of the game display.
        """
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active_effects = []  # List to hold all currently running effects
        self.effect_paths = self.load_effect_paths()

    def load_effect_paths(self):
        """Loads and maps the file paths for all available effect types."""
        return {
            "EXPLOSION_1": "assets/images/Effect/explosion01.png",
            "EXPLOSION_2": "assets/images/Effect/explosion02.png",
            "EXPLOSION_3": "assets/images/Effect/explosion03.png",
        }

    # -----------------------------------------------------------
    # Frame Cycle
    # -----------------------------------------------------------
    def update(self, dt):
        """
        Updates the state and animation of all active effects.

        Args:
            dt (float): Delta time since the last frame.
        """
        for e in self.active_effects:
            e.update(dt)

        # Remove effects that have completed their lifecycle
        self.active_effects = [e for e in self.active_effects if e.is_active]

    def draw(self, surface):
        """
        Renders all active effects onto the given surface, ordered by layer.

        Args:
            surface (pygame.Surface): The surface to draw the effects onto.
        """
        # Sort effects by layer to ensure correct rendering order
        for e in sorted(self.active_effects, key=lambda x: x.layer):
            e.draw(surface)

    # -----------------------------------------------------------
    # Creation Methods
    # -----------------------------------------------------------
    def create_explosion(self, position, effect_type, layer=100):
        """
        Creates and registers a new explosion effect at the specified position.

        Args:
            position (tuple[float, float]): (x, y) coordinates of the explosion center.
            effect_type (str): Key identifying the desired explosion sprite path.
            layer (int, optional): Rendering layer priority. Defaults to 100.

        Returns:
            ExplosionEffect | None: The created effect instance or None if type is invalid.
        """
        if effect_type not in self.effect_paths:
            DebugLogger.warn(
                f"Unknown effect type '{effect_type}'. "
                f"Available: {list(self.effect_paths.keys())}"
            )
            return None

        image_path = self.effect_paths[effect_type]
        x, y = position

        explosion = ExplosionEffect(x, y, image_path, layer)

        # Add to active list only if the effect is ready to run
        if explosion.is_active:
            self.active_effects.append(explosion)

        return explosion

    def get_random_explosion(self):
        """
        Loads the list of available explosion types and returns one randomly.
        """
        return random.choice(list(self.effect_paths.keys()))