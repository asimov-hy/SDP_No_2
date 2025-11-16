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

from src.core.debug.debug_logger import DebugLogger
from src.scenes.start_scene import StartScene
from src.scenes.game.game_scene import GameScene


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
            draw_manager: Reference to the DrawManager responsible for rendering entities_animation.
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

        # Cached active instance (Hot Path Cache)
        self._active_instance = None

        # Activate default starting scene
        self.set_scene("StartScene")

    # ===========================================================
    # Scene Control
    # ===========================================================
    def register_scene(self, name, scene_class):
        """Register a scene class by name."""
        self.scenes[name] = scene_class
        DebugLogger.state(f"Registered scene '{name}'")

    def set_scene(self, name: str, **scene_data):
        """
        Switch to another scene by name with proper lifecycle management.

        Args:
            name: Scene name
            **scene_data: Data to pass to on_load() hook
        """
        from src.core.runtime.scene_state import SceneState

        prev = getattr(self, "active_scene", None)

        if name not in self.scenes:
            DebugLogger.warn(f"Unknown scene: '{name}'")
            return

        # === STEP 1: Exit old scene ===
        if self._active_instance and hasattr(self._active_instance, "on_exit"):
            DebugLogger.state(f"Exiting {self._active_instance.__class__.__name__}")
            self._active_instance.state = SceneState.EXITING
            self._active_instance.on_exit()

        # Transition logging
        prev_class = self._get_scene_name(prev)
        next_class = self._get_scene_name(name) or name

        if prev_class:
            DebugLogger.system(f"Transitioning [{prev_class}] → [{next_class}]")
        else:
            DebugLogger.system(f"Loading Initial Scene: [{next_class}]")

        # === STEP 2: Create/retrieve instance ===
        if isinstance(self.scenes[name], type):
            scene_class = self.scenes[name]
            self.scenes[name] = scene_class(self)

        self._active_instance = self.scenes[name]
        self.active_scene = name

        # === STEP 3: Load new scene ===
        self._active_instance.state = SceneState.LOADING
        if hasattr(self._active_instance, "on_load"):
            DebugLogger.state(f"Loading {next_class}")
            self._active_instance.on_load(**scene_data)

        # === STEP 4: Activate scene ===
        self._active_instance.state = SceneState.ACTIVE
        DebugLogger.section(f"Active Scene: {next_class}")

        # === STEP 5: Enter scene ===
        if hasattr(self._active_instance, "on_enter"):
            DebugLogger.state(f"Entering {next_class}")
            self._active_instance.on_enter()

    def pause_active_scene(self):
        """Pause the currently active scene."""
        from src.core.runtime.scene_state import SceneState

        if not self._active_instance:
            return

        if self._active_instance.state != SceneState.ACTIVE:
            return

        DebugLogger.state(f"Pausing {self._active_instance.__class__.__name__}")
        self._active_instance.state = SceneState.PAUSED

        if hasattr(self._active_instance, "on_pause"):
            self._active_instance.on_pause()

    def resume_active_scene(self):
        """Resume the currently paused scene."""
        from src.core.runtime.scene_state import SceneState

        if not self._active_instance:
            return

        if self._active_instance.state != SceneState.PAUSED:
            return

        DebugLogger.state(f"Resuming {self._active_instance.__class__.__name__}")
        self._active_instance.state = SceneState.ACTIVE

        if hasattr(self._active_instance, "on_resume"):
            self._active_instance.on_resume()

    # ===========================================================
    # Event, Update, Draw Delegation
    # ===========================================================
    def handle_event(self, event):
        """
        Forward a pygame event to the active scene.

        Args:
            event (pygame.event.Event): The event object to be handled.
        """
        if self._active_instance:
            self._active_instance.handle_event(event)

    def update(self, dt: float):
        """
        Update the currently active scene (only if ACTIVE).

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """
        from src.core.runtime.scene_state import SceneState

        if self._active_instance and self._active_instance.state == SceneState.ACTIVE:
            self._active_instance.update(dt)

    def draw(self, draw_manager):
        """
        Render the active scene using the provided DrawManager.

        Args:
            draw_manager: The DrawManager instance responsible for queuing draw calls.
        """
        if self._active_instance:
            self._active_instance.draw(draw_manager)

    def _get_scene_name(self, scene_key):
        """Return a readable scene name from the registry."""
        if scene_key not in self.scenes:
            return None
        scene_obj = self.scenes[scene_key]
        return scene_obj.__name__ if isinstance(scene_obj, type) else scene_obj.__class__.__name__
