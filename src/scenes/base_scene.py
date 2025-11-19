"""
base_scene.py
-------------
Abstract base class for all scenes.
Defines the interface and common lifecycle management.
"""

from abc import ABC, abstractmethod
from src.scenes.scene_state import SceneState


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