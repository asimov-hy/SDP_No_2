"""
scene_manager.py
----------------
Handles switching and updating different scenes such as StartScreen, GameScreen, and PauseScreen.

Responsibilities
----------------
- Maintain a registry of all available scenes.
- Handle transitions between scenes.
- Forward events, updates, and draw calls to the active scene.
"""

from src.core.utils.debug_logger import DebugLogger
from src.scenes.start_scene import StartScene
from src.scenes.game_scene import GameScene


class SceneManager:
    """Coordinates scene transitions and delegates update/draw logic."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, display_manager, input_manager, draw_manager):
        """
        Initialize all scenes and set the starting scene.

        Args:
            display_manager: Reference to the DisplayManager handling rendering.
            input_manager: Reference to the InputManager managing user input.
            draw_manager: Reference to the DrawManager responsible for rendering entities.
        """

        self.display = display_manager
        self.input_manager = input_manager
        self.draw_manager = draw_manager
        DebugLogger.init_entry("SceneManager")

        # Create scene instances
        DebugLogger.init_sub("Setting up initial scene")
        self.scenes = {
            "StartScene": StartScene,
            "GameScene": GameScene
        }

        # Activate default starting scene
        self.set_scene("StartScene", silent=True)

    # ===========================================================
    # Scene Control
    # ===========================================================
    def register_scene(self, name, scene_class):
        """Register a scene class by name."""
        self.scenes[name] = scene_class
        DebugLogger.state(f"Registered scene '{name}'")

    def set_scene(self, name: str, silent=False):
        """
        Switch to another scene by name.

        Args:
            name (str): Name of the target scene (e.g., "StartScene").
            silent (bool): If True, suppress transition log output.

        Notes:
            Logs scene transitions and ignores invalid scene requests.
        """

        prev = getattr(self, "active_scene", None)
        self.active_scene = name

        if name not in self.scenes:
            DebugLogger.warn(f"Unknown scene: '{name}'")
            return

        if isinstance(self.scenes[name], type):
            scene_class = self.scenes[name]
            self.scenes[name] = scene_class(self)

        # Transition formatting
        new_class = self._get_scene_name(name)
        prev_class = self._get_scene_name(prev)

        if prev_class and not silent:
            DebugLogger.system(f"Scene Transition [{prev_class}] → [{new_class}]")

        # Log the current active scene
        DebugLogger.section(f"Set Scene: {new_class}")

    # ===========================================================
    # Event, Update, Draw Delegation
    # ===========================================================
    def handle_event(self, event):
        """
        Forward a pygame event to the active scene.

        Args:
            event (pygame.event.Event): The event object to be handled.
        """
        self.scenes[self.active_scene].handle_event(event)

    def update(self, dt: float):
        """
        Update the currently active scene.

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """
        self.scenes[self.active_scene].update(dt)

    def draw(self, draw_manager):
        """
        Render the active scene using the provided DrawManager.

        Args:
            draw_manager: The DrawManager instance responsible for queuing draw calls.
        """
        self.scenes[self.active_scene].draw(draw_manager)

    def _get_scene_name(self, scene_key):
        """Return a readable scene name from the registry."""
        if scene_key not in self.scenes:
            return None
        scene_obj = self.scenes[scene_key]
        return scene_obj.__name__ if isinstance(scene_obj, type) else scene_obj.__class__.__name__
