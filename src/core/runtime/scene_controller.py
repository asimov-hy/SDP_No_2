"""
scene_controller.py
-------------------
Base class for scene controllers that handle specific responsibilities.
"""

from abc import ABC


class SceneController(ABC):
    """
    Base class for controllers that manage a portion of a scene's logic.

    Controllers separate concerns and enable multi-developer safety.
    """

    def __init__(self, scene):
        """
        Initialize controller with reference to parent scene.

        Args:
            scene: The parent scene this controller belongs to
        """
        self.scene = scene

    def update(self, dt: float):
        """
        Update this controller's logic.

        Args:
            dt: Delta time in seconds
        """
        pass

    def draw(self, draw_manager):
        """
        Render this controller's visuals.

        Args:
            draw_manager: DrawManager instance for queueing draw calls
        """
        pass

    def handle_event(self, event):
        """
        Handle input events for this controller.

        Args:
            event: pygame.event.Event to process
        """
        pass