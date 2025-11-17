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

import pygame
from src.core.debug.debug_logger import DebugLogger
from src.scenes.start.start_scene import StartScene
from src.scenes.game.game_scene import GameScene
from src.core.runtime.scene_state import SceneState
from src.scenes.settings.settings_scene import SettingsScene
from src.core.runtime.transitions.instant_transition import InstantTransition

class SceneManager:
    """Coordinates scene transitions and delegates update/draw logic."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, display_manager, input_manager, draw_manager):
        """
        Initialize scene registry with pooling support.
        """
        self.display = display_manager
        self.input_manager = input_manager
        self.draw_manager = draw_manager
        DebugLogger.init_entry("SceneManager")

        # Scene registry: stores classes OR instances
        self.scenes = {}

        # Pooling config: which scenes get reused vs recreated
        self.pooled_scenes = set()

        # Cached active instance (Hot Path Cache)
        self._active_instance = None

        # Transition system
        self._active_transition = None
        self._transition_old_scene = None
        self._transition_new_scene = None

        # Register scenes with pooling preferences
        DebugLogger.init_sub("Registering scenes")
        self.register_scene("StartScene", StartScene, pooled=True)
        self.register_scene("GameScene", GameScene, pooled=False)

        self.register_scene("StartScene", StartScene, pooled=True)
        self.register_scene("GameScene", GameScene, pooled=False)
        self.register_scene("SettingsScene", SettingsScene, pooled=True)

        # Activate default starting scene
        self.set_scene("StartScene")

    # ===========================================================
    # Scene Control
    # ===========================================================
    def register_scene(self, name, scene_class, pooled=False):
        """
        Register a scene class with pooling preference.

        Args:
            name: Scene identifier
            scene_class: Class to instantiate
            pooled: If True, reuse instance; if False, create fresh each time
        """
        self.scenes[name] = scene_class

        if pooled:
            self.pooled_scenes.add(name)
            DebugLogger.state(f"Registered scene '{name}' (POOLED)")
        else:
            DebugLogger.state(f"Registered scene '{name}' (FRESH)")

    def set_scene(self, name: str, transition=None, **scene_data):
        """
        Switch to another scene with optional transition.

        Args:
            name: Scene name
            transition: ITransition instance (None = instant)
            **scene_data: Data to pass to on_load() hook
        """

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
            # First time loading this scene - instantiate it
            scene_class = self.scenes[name]
            instance = scene_class(self)

            # Store instance only if pooled
            if name in self.pooled_scenes:
                self.scenes[name] = instance
                DebugLogger.state(f"Pooling {next_class} instance")
            else:
                # Don't store - will recreate next time
                instance = scene_class(self)
                DebugLogger.state(f"Creating fresh {next_class} instance")

            self._active_instance = instance
        else:
            # Pooled scene - reuse existing instance
            self._active_instance = self.scenes[name]
            DebugLogger.state(f"Reusing pooled {next_class} instance")

            # Call reset() if available
            if hasattr(self._active_instance, "reset"):
                self._active_instance.reset()

        self.active_scene = name

        # === STEP 3: Load new scene ===
        self._active_instance.state = SceneState.LOADING
        if hasattr(self._active_instance, "on_load"):
            DebugLogger.state(f"Loading {next_class}")
            self._active_instance.on_load(**scene_data)

        # === STEP 4: Activate scene ===
        self._active_instance.state = SceneState.ACTIVE
        DebugLogger.section(f"Active Scene: {next_class}")

        # === STEP 4.5: Handle transition ===
        if transition is not None:
            self._active_instance.state = SceneState.TRANSITIONING
            self._active_transition = transition
            self._transition_old_scene = prev  # May be None on first load
            self._transition_new_scene = self._active_instance
            DebugLogger.state(f"Starting transition: {transition.__class__.__name__}")
            # Don't activate yet - transition will handle it
            return

        # === STEP 5: Enter scene ===
        if hasattr(self._active_instance, "on_enter"):
            DebugLogger.state(f"Entering {next_class}")
            self._active_instance.on_enter()

        # === STEP 6: Auto-switch input context ===
        if hasattr(self._active_instance, "input_context"):
            self.input_manager.set_context(self._active_instance.input_context)

    def pause_active_scene(self):
        """Pause the currently active scene."""

        if not self._active_instance:
            return

        if self._active_instance.state != SceneState.ACTIVE:
            return

        DebugLogger.state(f"Pausing {self._active_instance.__class__.__name__}")
        self._active_instance.state = SceneState.PAUSED

        if hasattr(self._active_instance, "on_pause"):
            self._active_instance.on_pause()

        self.input_manager.set_context("ui")

    def resume_active_scene(self):
        """Resume the currently paused scene."""

        if not self._active_instance:
            return

        if self._active_instance.state != SceneState.PAUSED:
            return

        DebugLogger.state(f"Resuming {self._active_instance.__class__.__name__}")
        self._active_instance.state = SceneState.ACTIVE

        if hasattr(self._active_instance, "on_resume"):
            self._active_instance.on_resume()

        # Restore scene's original input context
        if hasattr(self._active_instance, "input_context"):
            self.input_manager.set_context(self._active_instance.input_context)

    # ===========================================================
    # Event, Update, Draw Delegation
    # ===========================================================
    def handle_event(self, event):
        """
        Forward a pygame event to the active scene.

        Args:
            event (pygame.event.Event): The event object to be handled.
        """

        # Global pause toggle (ESC key)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from src.core.runtime.scene_state import SceneState

            if self._active_instance:
                if self._active_instance.state == SceneState.ACTIVE:
                    self.pause_active_scene()
                elif self._active_instance.state == SceneState.PAUSED:
                    self.resume_active_scene()
            return  # Don't forward ESC to scene

        if self._active_instance:
            self._active_instance.handle_event(event)

    def update(self, dt: float):
        """
        Update the currently active scene or active transition.

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """

        # Handle active transition
        if self._active_transition:
            transition_complete = self._active_transition.update(dt)

            if transition_complete:
                # Transition finished - activate new scene
                DebugLogger.state("Transition complete")
                self._active_transition = None
                self._transition_old_scene = None
                self._transition_new_scene = None

                # Activate and enter new scene
                self._active_instance.state = SceneState.ACTIVE
                if hasattr(self._active_instance, "on_enter"):
                    self._active_instance.on_enter()

                # Auto-switch input context
                if hasattr(self._active_instance, "input_context"):
                    self.input_manager.set_context(self._active_instance.input_context)
            return

        # Normal scene update (only if ACTIVE)
        if self._active_instance and self._active_instance.state == SceneState.ACTIVE:
            self._active_instance.update(dt)

    def draw(self, draw_manager):
        """
        Render the active scene or transition effect.

        Args:
            draw_manager: The DrawManager instance responsible for queuing draw calls.
        """
        # Render transition if active
        if self._active_transition:
            self._active_transition.draw(
                draw_manager,
                self._transition_old_scene,
                self._transition_new_scene
            )
            return

        # Normal scene rendering
        if self._active_instance:
            self._active_instance.draw(draw_manager)

    def _get_scene_name(self, scene_key):
        """Return a readable scene name from the registry."""
        if scene_key not in self.scenes:
            return None
        scene_obj = self.scenes[scene_key]
        return scene_obj.__name__ if isinstance(scene_obj, type) else scene_obj.__class__.__name__
