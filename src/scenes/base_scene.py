"""
base_scene.py
-------------
Abstract base class for all scenes.

Provides:
- Lifecycle hooks (load, enter, pause, resume, exit)
- Background system with scene-local ownership
- Service locator access
- Abstract methods for update, draw, handle_event
"""

from abc import ABC, abstractmethod
from src.scenes import SceneState
from src.core.debug.debug_logger import DebugLogger
from src.graphics.background_manager import BackgroundManager
from src.core.runtime import Display


class BaseScene(ABC):
    """
    Base class for all scenes.

    Attributes:
        state: Current lifecycle state
        input_context: Input context for this scene ("gameplay" or "ui")
        services: ServiceLocator for accessing managers and systems
        bg_manager: Scene-owned background manager (optional)
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
        self.input_manager = services.input_manager
        self.draw_manager = services.draw_manager

        # Scene-owned background (initialized via _setup_background)
        self.bg_manager = None

    # ===========================================================
    # Properties
    # ===========================================================

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
    # Background System
    # ===========================================================

    def _setup_background(self, config):
        """
        Setup scrolling background for this scene.

        Scene owns the BackgroundManager instance. DrawManager receives
        a reference for rendering but does not own it.

        Args:
            config: Background configuration dict with 'layers' list
                    Example: {"layers": [{"image": "path.png", "scroll_speed": [0, 30]}]}
        """

        if not config or "layers" not in config:
            DebugLogger.warn(f"No background config for {self.__class__.__name__}")
            return

        # Create scene-owned background manager
        self.bg_manager = BackgroundManager((Display.WIDTH, Display.HEIGHT))

        # Add layers from config
        for layer_config in config.get("layers", []):
            self.bg_manager.add_layer(
                image_path=layer_config.get("image", ""),
                scroll_speed=tuple(layer_config.get("scroll_speed", [0, 30])),
                parallax=tuple(layer_config.get("parallax", [0.4, 0.6]))
            )

        # Pass reference to draw manager for rendering
        self.draw_manager.bg_manager = self.bg_manager

        DebugLogger.init_sub(
            f"Background initialized for {self.__class__.__name__} "
            f"({self.bg_manager.layer_count} layers)"
        )

    def _update_background(self, dt, focal_point=None):
        """
        Update scrolling background.

        Args:
            dt: Delta time in seconds
            focal_point: (x, y) position for parallax (e.g., player position)
        """
        if self.bg_manager:
            self.bg_manager.update(dt, focal_point)

    def _clear_background(self):
        """Remove background when leaving scene."""
        if self.bg_manager:
            self.bg_manager.clear_layers()
            self.bg_manager = None

        # Clear draw manager reference
        if self.draw_manager:
            self.draw_manager.bg_manager = None

        DebugLogger.action(f"Background cleared for {self.__class__.__name__}")

    # ===========================================================
    # Background Controls (Convenience wrappers)
    # ===========================================================

    def pause_background(self):
        """Pause background scrolling."""
        if self.bg_manager:
            self.bg_manager.pause()

    def resume_background(self):
        """Resume background scrolling."""
        if self.bg_manager:
            self.bg_manager.resume()

    def set_background_scroll_speed(self, layer_index, speed):
        """
        Set scroll speed for a background layer.

        Args:
            layer_index: Layer index (0 = bottom)
            speed: (x, y) tuple in pixels/second
        """
        if self.bg_manager:
            self.bg_manager.set_scroll_speed(layer_index, speed)

    def set_background_parallax(self, layer_index, parallax):
        """
        Set parallax factor for a background layer.

        Args:
            layer_index: Layer index (0 = bottom)
            parallax: (x, y) tuple (0.0 to 1.0)
        """
        if self.bg_manager:
            self.bg_manager.set_parallax(layer_index, parallax)

    @property
    def background_paused(self):
        """Check if background scrolling is paused."""
        if self.bg_manager:
            return self.bg_manager.paused
        return False

    # ===========================================================
    # Abstract Methods (Must implement in subclasses)
    # ===========================================================

    @abstractmethod
    def update(self, dt: float):
        """
        Update scene logic.

        Args:
            dt: Delta time in seconds
        """
        pass

    @abstractmethod
    def draw(self, draw_manager):
        """
        Render the scene.

        Args:
            draw_manager: DrawManager instance for queuing draws
        """
        pass

    @abstractmethod
    def handle_event(self, event):
        """
        Handle input events.

        Args:
            event: pygame event object
        """
        pass
