"""
i_transition.py
---------------
Interface for scene transitions.
"""

from abc import ABC, abstractmethod


class ITransition(ABC):
    """Base interface for scene transitions."""

    def __init__(self, duration: float = 0.0):
        """
        Initialize transition.

        Args:
            duration: Transition length in seconds (0.0 = instant)
        """
        self.duration = duration
        self.elapsed = 0.0
        self.complete = False

    @abstractmethod
    def update(self, dt: float) -> bool:
        """
        Update transition animation.

        Args:
            dt: Delta time in seconds

        Returns:
            True if transition complete, False otherwise
        """
        pass

    @abstractmethod
    def draw(self, draw_manager, old_scene, new_scene):
        """
        Render transition effect.

        Args:
            draw_manager: DrawManager instance
            old_scene: Scene being exited (may be None)
            new_scene: Scene being entered
        """
        pass

    def reset(self):
        """Reset transition to initial state."""
        self.elapsed = 0.0
        self.complete = False