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
        self.input = input_manager
        self.draw_manager = draw_manager
        DebugLogger.init("║{:<59}║".format(f"\t[SceneManager][INIT]\t→ Initialized Core Systems"), show_meta=False)

        # Create scene instances
        self.scenes = {
            "START": StartScene,
            "GAME": GameScene
        }
        DebugLogger.init("║{:<59}║".format(f"\t[SceneManager][INIT]\t→ Setting Up Scenes"), show_meta=False)

        # Activate default starting scene
        self.set_scene("START", silent=True)
        DebugLogger.init("║{:<57}║".format(f"\t\t└─ [StartScene][INIT]\t→ Active Scene: {self.active_scene}"), show_meta=False)

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
            name (str): Identifier of the target scene.

        Notes:
            Logs scene transitions and ignores invalid scene requests.
        """
        prev = getattr(self, "active_scene", None)
        self.active_scene = name

        # Transition formatting
        if not silent:
            if prev:
                DebugLogger.action(f"Begin Scene Transition [{prev.upper()}] → [{name.upper()}]")
            else:
                DebugLogger.action(f"Initializing Scene: [{name.upper()}]")

        if name not in self.scenes:
            DebugLogger.warn(f"Attempted to switch to unknown scene: '{name}'")
            return

        if isinstance(self.scenes[name], type):
            scene_class = self.scenes[name]
            self.scenes[name] = scene_class(self)
            if not silent:
                DebugLogger.action(f"Scene [{name}] instantiated")

        # Log active scene
        width = 60
        if not silent:
            DebugLogger.state("─" * width)
            DebugLogger.state(f"{'Active Scene: ' + self.active_scene:^{width}}")
            DebugLogger.state("─" * width)

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