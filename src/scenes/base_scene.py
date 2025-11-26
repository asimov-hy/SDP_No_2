"""
base_scene.py
-------------
Abstract base class for all scenes.
Defines the interface and common lifecycle management.
"""

from abc import ABC, abstractmethod
from src.scenes.scene_state import SceneState
from src.core.debug.debug_logger import DebugLogger


class BaseScene(ABC):
    """
    Base class for all scenes.

    Attributes:
        state: Current lifecycle state
        input_context: Which input context this scene uses ("gameplay" or "ui")
        services: ServiceLocator for accessing managers and systems
    """

    def __init__(self, services):
        """
        Initialize scene with service locator.

        Args:
            services: ServiceLocator instance for dependency injection
        """
        self.services = services
        self.state = SceneState.INACTIVE
        self.input_context = "ui"  # Default to UI, override in subclasses

        # Convenience access to frequently used managers
        self.scene_manager = services.scene_manager
        # self.display is now a property (see below)
        self.input_manager = services.input_manager
        self.draw_manager = services.draw_manager

    @property
    def display(self):
        """Access display manager."""
        return self.services.display_manager

    # ===========================================================
    # Lifecycle Hooks (Override in subclasses)
    # ===========================================================

    def on_load(self, **scene_data):
        """Called once when scene is first created or reloaded."""
        pass

    def on_enter(self):
        """Called when scene becomes active."""
        pass

    def on_pause(self):
        """Called when scene is paused (e.g., pause menu appears)."""
        pass

    def on_resume(self):
        """Called when scene resumes from pause."""
        pass

    def on_exit(self):
        """Called before transitioning to another scene."""
        pass

    # ===========================================================
    # Background System (NEW)
    # ===========================================================
    def _setup_background(self, config=None):
        """
        Setup scrolling background for this scene.

        Args:
            config: Background configuration dict with 'layers' list
                    If None, uses default background
        """
        from src.graphics.background_manager import BackgroundManager, DEFAULT_BACKGROUND_CONFIG
        from src.core.runtime.game_settings import Display

        # Use default if no config provided
        if config is None:
            config = DEFAULT_BACKGROUND_CONFIG

        # Get draw manager
        draw_manager = self.draw_manager

        # Create background manager
        bg_manager = BackgroundManager((Display.WIDTH, Display.HEIGHT))

        # Add layers from config
        layers = config.get("layers", [])
        for layer_config in layers:
            bg_manager.add_layer(
                image_path=layer_config.get("image", ""),
                scroll_speed=tuple(layer_config.get("scroll_speed", [0, 30])),
                parallax=tuple(layer_config.get("parallax", [0.4, 0.6]))
            )

        # Attach to draw manager
        draw_manager.bg_manager = bg_manager
        DebugLogger.init_sub(f"Background initialized for {self.__class__.__name__}")

    def _update_background(self, dt, focal_point=None):
        """
        Update scrolling background.

        Args:
            dt: Delta time
            focal_point: (x, y) position for parallax (e.g., player position)
        """
        draw_manager = self.draw_manager
        if draw_manager and draw_manager.bg_manager:
            draw_manager.bg_manager.update(dt, focal_point)

    def _clear_background(self):
        """Remove background (e.g., when leaving scene)."""
        draw_manager = self.draw_manager
        if draw_manager:
            draw_manager.bg_manager = None

    # ===========================================================
    # Standard Methods (Must implement in subclasses)
    # ===========================================================

    @abstractmethod
    def update(self, dt: float):
        """Update scene logic."""
        pass

    @abstractmethod
    def draw(self, draw_manager):
        """Render the scene."""
        pass

    @abstractmethod
    def handle_event(self, event):
        """Handle input events."""
        pass