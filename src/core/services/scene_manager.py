"""
scene_manager.py
----------------
Simplified scene coordinator - direct class registration.
"""

from src.core.debug.debug_logger import DebugLogger
from src.scenes.scene_state import SceneState
from src.core.services.service_locator import ServiceLocator
from src.core.runtime.session_stats import update_session_stats
from src.systems.entity_management.entity_registry import EntityRegistry
from src.systems.level.level_registry import LevelRegistry

# Import scene classes
from src.scenes.main_menu_scene import MainMenuScene
from src.scenes.campaign_select_scene import CampaignSelectScene
from src.scenes.game_scene import GameScene
from src.scenes.settings_scene import SettingsScene


class SceneManager:
    """Coordinates scene transitions and delegates update/draw logic."""

    def __init__(self, display_manager, input_manager, draw_manager, ui_manager):
        """Initialize scene manager with direct scene registration."""
        self.display = display_manager
        self.input_manager = input_manager
        self.draw_manager = draw_manager
        self.ui_manager = ui_manager
        DebugLogger.init_entry("SceneManager")

        # Create service locator
        self.services = ServiceLocator(self)
        DebugLogger.init_sub("ServiceLocator initialized")

        # Register global systems
        self.services.register_global("session_stats", update_session_stats())
        self.services.register_global("entity_registry", EntityRegistry)
        self.services.register_global("level_registry", LevelRegistry)
        DebugLogger.init_sub("Registered global systems")

        # Load level registry config at startup
        LevelRegistry.load_config("campaigns.json")
        DebugLogger.init_sub("Level registry loaded")

        # Pre-load entity configs once at startup
        EntityRegistry.load_entity_data("entities/enemies.json")
        EntityRegistry.load_entity_data("entities/items.json")
        DebugLogger.init_sub("Entity configs pre-loaded")

        # Scene registry - map names to classes
        self.scene_classes = {
            "MainMenu": MainMenuScene,
            "CampaignSelect": CampaignSelectScene,
            "Game": GameScene,
            "Settings": SettingsScene,
        }

        # Active scene tracking
        self._active_scene = None
        self._active_name = None

        # Scene stack for pause/settings
        self._scene_stack = []

        # Transition system
        self._active_transition = None
        self._transition_old_scene = None
        self._transition_new_scene = None

        DebugLogger.init_sub(f"Registered scenes: {list(self.scene_classes.keys())}")

        # Start with main menu
        self.set_scene("MainMenu")

    # ===========================================================
    # Scene Control
    # ===========================================================
    def set_scene(self, name: str, transition=None, **scene_data):
        """
        Switch to another scene.

        Args:
            name: Scene name ("MainMenu", "Game", etc.)
            transition: ITransition instance (None = instant)
            **scene_data: Data to pass to on_load() hook
        """
        if name not in self.scene_classes:
            DebugLogger.warn(f"Unknown scene: '{name}'")
            return

        # === STEP 1: Exit old scene ===
        if self._active_scene:
            DebugLogger.state(f"Exiting {self._active_name}")
            self._active_scene.state = SceneState.EXITING
            self._active_scene.on_exit()

            # Clear scene-local entities
            self.services.clear_entities()

        # Log transition
        prev_name = self._active_name or "None"
        DebugLogger.system(f"Transitioning [{prev_name}] → [{name}]")

        # === STEP 2: Create new scene ===
        scene_class = self.scene_classes[name]
        new_scene = scene_class(self.services)

        self._active_scene = new_scene
        self._active_name = name

        # === STEP 3: Load new scene ===
        new_scene.state = SceneState.LOADING
        DebugLogger.state(f"Loading {name}")
        new_scene.on_load(**scene_data)

        # === STEP 4: Activate ===
        new_scene.state = SceneState.ACTIVE
        DebugLogger.section(f"Active Scene: {name}")

        # === STEP 5: Handle transition ===
        if transition is not None:
            new_scene.state = SceneState.TRANSITIONING
            self._active_transition = transition
            self._transition_old_scene = self._active_scene
            self._transition_new_scene = new_scene
            DebugLogger.state(f"Starting transition: {transition.__class__.__name__}")
            return

        # === STEP 6: Enter scene ===
        DebugLogger.state(f"Entering {name}")
        new_scene.on_enter()

        # === STEP 7: Switch input context ===
        self.input_manager.set_context(new_scene.input_context)

    def pause_active_scene(self):
        """Pause the currently active scene."""
        if not self._active_scene:
            return

        if self._active_scene.state != SceneState.ACTIVE:
            return

        DebugLogger.state(f"Pausing {self._active_name}")
        self._active_scene.state = SceneState.PAUSED

        self._active_scene.on_pause()

        self.input_manager.set_context("ui")

    def resume_active_scene(self):
        """Resume the currently paused scene."""
        if not self._active_scene:
            return

        if self._active_scene.state != SceneState.PAUSED:
            return

        DebugLogger.state(f"Resuming {self._active_name}")
        self._active_scene.state = SceneState.ACTIVE

        self._active_scene.on_resume()

        # Restore scene's input context
        self.input_manager.set_context(self._active_scene.input_context)

    def push_scene(self, name: str, **scene_data):
        """
        Push current scene to stack and switch to new scene.
        Used for Settings overlay while preserving Game state.
        """
        if self._active_scene:
            # Save current scene to stack
            self._scene_stack.append({
                'scene': self._active_scene,
                'name': self._active_name
            })
            DebugLogger.state(f"Pushed {self._active_name} to stack")

        # Switch to new scene
        self.set_scene(name, **scene_data)

    # In scene_manager.py, modify pop_scene:

    def pop_scene(self):
        """Return to previous scene from stack."""
        if not self._scene_stack:
            DebugLogger.warn("No scene to pop from stack")
            return

        # Exit current scene
        if self._active_scene:
            self._active_scene.state = SceneState.EXITING
            self._active_scene.on_exit()

        # Restore previous scene
        prev = self._scene_stack.pop()
        self._active_scene = prev['scene']
        self._active_name = prev['name']

        DebugLogger.state(f"Popped back to {self._active_name} (state: {self._active_scene.state})")

        # CRITICAL: If returning to paused game, restore pause UI
        if self._active_name == "Game" and self._active_scene.state == SceneState.PAUSED:
            self._active_scene.on_pause()  # Re-show pause overlay

        # Restore input context
        if self._active_scene.state == SceneState.PAUSED:
            self.input_manager.set_context("ui")
        else:
            self.input_manager.set_context(self._active_scene.input_context)

    # ===========================================================
    # Event, Update, Draw Delegation
    # ===========================================================

    def handle_event(self, event):
        """Forward event to active scene."""
        if self._active_scene:
            self._active_scene.handle_event(event)

    def update(self, dt: float):
        """Update active scene or transition."""
        # Handle active transition
        if self._active_transition:
            transition_complete = self._active_transition.update(dt)

            if transition_complete:
                DebugLogger.state("Transition complete")
                self._active_transition = None
                self._transition_old_scene = None
                self._transition_new_scene = None

                # Activate and enter new scene
                self._active_scene.state = SceneState.ACTIVE
                self._active_scene.on_enter()

                # Switch input context
                self.input_manager.set_context(self._active_scene.input_context)
            return

        # Handle pause toggle - only in Game scene
        if self._active_name == "Game":
            pause_pressed = False

            if self.input_manager.context == "gameplay":
                pause_pressed = self.input_manager.action_pressed("pause")
            elif self.input_manager.context == "ui":
                pause_pressed = self.input_manager.action_pressed("back")

            if pause_pressed:
                if self._active_scene.state == SceneState.ACTIVE:
                    self.pause_active_scene()
                    return
                elif self._active_scene.state == SceneState.PAUSED:
                    self.resume_active_scene()
                    return

        # Normal scene update (only if ACTIVE)
        if self._active_scene and self._active_scene.state in (SceneState.ACTIVE, SceneState.PAUSED):
            self._active_scene.update(dt)

    def draw(self, draw_manager):
        """Render active scene or transition."""
        # Render transition if active
        if self._active_transition:
            self._active_transition.draw(
                draw_manager,
                self._transition_old_scene,
                self._transition_new_scene
            )
            return

        # Normal scene rendering
        if self._active_scene:
            self._active_scene.draw(draw_manager)

    def get_player(self):
        return self.services.get_entity("player")
