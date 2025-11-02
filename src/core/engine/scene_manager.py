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
        from src.scenes.start_scene import StartScene
        from src.scenes.game_scene import GameScene
        # from src.scenes.pause_scene import PauseScene

        self.display = display_manager
        self.input = input_manager
        self.draw_manager = draw_manager

        # Create scene instances
        self.scenes = {
            "start": StartScene(self),
            "game": GameScene(self),
            # "pause": PauseScene(self)
        }

        # Default active scene
        self.active_scene = "start"
        DebugLogger.system("SceneManager", f"Initialized with active scene: {self.active_scene}")


    # ===========================================================
    # Scene Control
    # ===========================================================
    def set_scene(self, name: str):
        """
        Switch to another scene by name.

        Args:
            name (str): Identifier of the target scene.

        Notes:
            Logs scene transitions and ignores invalid scene requests.
        """
        if name in self.scenes:
            prev = self.active_scene
            self.active_scene = name
            DebugLogger.action("SceneManager", f"Scene switched: {prev} → {name}")
        else:
            DebugLogger.warn("SceneManager", f"Attempted to switch to unknown scene: '{name}'")

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