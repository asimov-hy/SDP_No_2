"""
input_manager.py
----------------
Handles all input sources including keyboard and (future) controller support.

Responsibilities
----------------
- Maintain current input state for movement and actions.
- Support customizable key bindings.
- Merge keyboard and controller input into a single movement vector.
"""
import pygame
from src.core.debug.debug_logger import DebugLogger

# ===========================================================
# Default Key Bindings
# ===========================================================
DEFAULT_KEY_BINDINGS = {
    "gameplay": {
        "move_left": [pygame.K_LEFT, pygame.K_a],
        "move_right": [pygame.K_RIGHT, pygame.K_d],
        "move_up": [pygame.K_UP, pygame.K_w],
        "move_down": [pygame.K_DOWN, pygame.K_s],
        "attack": [pygame.K_SPACE],
        "bomb": [pygame.K_LSHIFT, pygame.K_RSHIFT],
        "pause": [pygame.K_ESCAPE],
    },
    "ui": {
        "navigate_up": [pygame.K_UP, pygame.K_w],
        "navigate_down": [pygame.K_DOWN, pygame.K_s],
        "navigate_left": [pygame.K_LEFT, pygame.K_a],
        "navigate_right": [pygame.K_RIGHT, pygame.K_d],
        "confirm": [pygame.K_RETURN, pygame.K_SPACE],
        "back": [pygame.K_ESCAPE],
    },
    "system": {  # !!SHOULD NOT OVERLAP WITH OTHER KEYBINDING GROUPS!!
        "toggle_debug": [pygame.K_F3],
        "toggle_fullscreen": [pygame.K_F11],
    },
}


class InputManager:
    """Processes player input from keyboard and (optionally) controllers."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, key_bindings=None):
        """
        Initialize keyboard and optional controller input.

        Args:
            key_bindings (dict, optional): Custom key-action mapping.
                Defaults to DEFAULT_KEY_BINDINGS if not provided.
        """
        self.key_bindings = key_bindings or DEFAULT_KEY_BINDINGS
        self.context = "gameplay"  # active context ("gameplay" or "ui")

        # Build flat lookup tables at init
        self._key_to_action_cache = {}  # {context: {pygame_key: action_name}}
        self._active_lookup = None      # Points to current context's lookup
        self._build_key_caches()

        self._context_keys = {}        # {context: [pygame_keys]}
        self._active_keys = []         # Current context's keys only
        self._build_key_lists()

        self._switch_active_cache("gameplay")

        DebugLogger.init_entry("InputManager")

        # -------------------------------------------------------
        # Validate that system bindings do not overlap with others
        # -------------------------------------------------------
        self._validate_bindings()

        # -------------------------------------------------------
        # Controller setup
        # -------------------------------------------------------
        pygame.joystick.init()
        self.controller = None
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            DebugLogger.init_sub("Controller Input Initialized")
            DebugLogger.init_sub(f"Detected: {self.controller.get_name()}", level=2)

        self._has_controller = self.controller is not None

        DebugLogger.init_sub("Keyboard Input Initialized")

        # -------------------------------------------------------
        # Movement and gameplay state tracking
        # -------------------------------------------------------
        self.move = pygame.Vector2(0, 0)
        self._move_keyboard = pygame.Vector2(0, 0)
        self._move_controller = pygame.Vector2(0, 0)

        self._normalized_move = pygame.Vector2(0, 0)
        self._last_raw_move = pygame.Vector2(0, 0)
        self._normalized_dirty = True

        # Action registry - stores all action states
        self._actions = {
            # Gameplay actions
            "attack": {"pressed": False, "held": False},
            "bomb": {"pressed": False},
            "pause": {"pressed": False},

            # UI navigation actions
            "ui_up": {"pressed": False},
            "ui_down": {"pressed": False},
            "ui_left": {"pressed": False},
            "ui_right": {"pressed": False},
            "ui_confirm": {"pressed": False},
            "ui_back": {"pressed": False},
        }

    # ===========================================================
    # Validation
    # ===========================================================
    def _validate_bindings(self):
        """
        Ensure that system-level bindings do not overlap with gameplay or ui bindings.
        Logs a warning if any overlap is detected.
        """
        system_keys = {k for keys in self.key_bindings["system"].values() for k in keys}
        other_keys = {
            k for ctx in ("gameplay", "ui")
            for keys in self.key_bindings[ctx].values()
            for k in keys
        }
        overlap = system_keys & other_keys
        if overlap:
            DebugLogger.warn(f"[InputManager] Overlapping system keys detected: {overlap}")

    # ===========================================================
    # Context Management
    # ===========================================================
    def set_context(self, name: str):
        """
        Switch between contexts ("gameplay", "ui").

        Args:
            name (str): Name of the context to activate.
        """
        if name not in self.key_bindings:
            DebugLogger.warn(f"Unknown context: {name}")
            return
        self.context = name
        self._switch_active_cache(name)  # Just swap pointer
        DebugLogger.state(f"Context switched to [{name.upper()}]")

    def get_context(self):
        """Return the currently active input context."""
        return self.context

    # ===========================================================
    # Update Cycle
    # ===========================================================
    def update(self):
        """Poll all input sources once per frame."""
        if self.context == "ui":
            self._update_ui_navigation()
        else:
            self._update_gameplay_controls()

    # ===========================================================
    # Gameplay Input
    # ===========================================================
    def _update_gameplay_controls(self):
        """Poll keyboard/controller input for gameplay actions."""
        keys = pygame.key.get_pressed()

        # Directional input
        left = self._is_pressed("move_left", keys)
        right = self._is_pressed("move_right", keys)
        up = self._is_pressed("move_up", keys)
        down = self._is_pressed("move_down", keys)

        x = int(right) - int(left)
        y = int(down) - int(up)

        self._move_keyboard.update(x, y)

        # Actions
        # -----------------------------------------------------------
        # Attack input
        # -----------------------------------------------------------
        attack_state = self._is_pressed("attack", keys)
        self._actions["attack"]["pressed"] = attack_state
        self._actions["attack"]["held"] = attack_state

        self._actions["bomb"]["pressed"] = self._is_pressed("bomb", keys)
        self._actions["pause"]["pressed"] = self._is_pressed("pause", keys)

        # Merge controller input (unchanged)
        # self._update_controller()
        # self._merge_inputs()

        if self._has_controller:
            self._update_with_controller()
        else:
            self._update_keyboard_only()

        if self.move != self._last_raw_move:
            self._normalized_dirty = True
            self._last_raw_move.update(self.move)

        # Pause handling
        if self.pause_pressed:
            if hasattr(self, "scene_manager") and self.scene_manager._active_instance:
                self.scene_manager._active_instance.on_pause()
            else:
                DebugLogger.warn("Pause attempted but SceneManager not linked")

    def link_scene_manager(self, scene_manager):
        """Link SceneManager reference after initialization (dependency injection)."""
        self.scene_manager = scene_manager

    # ===========================================================
    # ui Navigation Input
    # ===========================================================

    def _update_ui_navigation(self):
        """Poll input for ui navigation."""
        keys = pygame.key.get_pressed()

        self._actions["ui_up"]["pressed"] = self._is_pressed("navigate_up", keys)
        self._actions["ui_down"]["pressed"] = self._is_pressed("navigate_down", keys)
        self._actions["ui_left"]["pressed"] = self._is_pressed("navigate_left", keys)
        self._actions["ui_right"]["pressed"] = self._is_pressed("navigate_right", keys)
        self._actions["ui_confirm"]["pressed"] = self._is_pressed("confirm", keys)
        self._actions["ui_back"]["pressed"] = self._is_pressed("back", keys)

        # ------------------------------------------
        # Controller support for ui
        # ------------------------------------------
        if self.controller:
            self._update_ui_controller()

    # ===========================================================
    # Controller Input
    # ===========================================================
    # def _update_controller(self):
    #     """
    #     Poll analog stick axes and controller buttons.
    #
    #     Notes:
    #         - Applies a deadzone to prevent drift.
    #         - Currently only supports primary analog movement.
    #     """
    #     if not self.controller:
    #         self._move_controller.update(0, 0)
    #         return
    #
    #     x_axis = self.controller.get_axis(0)
    #     y_axis = self.controller.get_axis(1)
    #     deadzone = 0.2
    #
    #     self._move_controller.x = x_axis if abs(x_axis) > deadzone else 0
    #     self._move_controller.y = y_axis if abs(y_axis) > deadzone else 0

    def _update_with_controller(self):
        """Hot path: keyboard + controller merging."""
        # Read controller axes
        x_axis = self.controller.get_axis(0)
        y_axis = self.controller.get_axis(1)
        deadzone = 0.2

        self._move_controller.x = x_axis if abs(x_axis) > deadzone else 0
        self._move_controller.y = y_axis if abs(y_axis) > deadzone else 0

        # Merge: controller overrides keyboard
        if self._move_controller.length_squared() > 0:
            self.move.update(self._move_controller)
        else:
            self.move.update(self._move_keyboard)

    def _update_keyboard_only(self):
        """Hot path: keyboard-only (no controller checks)."""
        self.move.update(self._move_keyboard)

    # ===========================================================
    # Input Merging and Query
    # ===========================================================
    # def _merge_inputs(self):
    #     """Combine keyboard and controller input cleanly."""
    #     if self._move_controller.length_squared() > 0:
    #         self.move = self._move_controller
    #     else:
    #         self.move = self._move_keyboard

    def _is_pressed(self, action, keys):
        """
        Check if any bound key for an action is pressed.

        Args:
            action (str): Name of the input action.
            keys (pygame.key.ScancodeWrapper): Current keyboard state.

        Returns:
            bool: True if any key bound to the action is pressed.
        """
        for key in self._active_keys:
            if keys[key] and self._active_lookup.get(key) == action:
                return True
        return False

    def _is_pressed_context(self, action, keys, context_dict):
        """
        Check if any bound key in a specific context dictionary is pressed.

        Used for system-level inputs that should always be available,
        regardless of gameplay/ui context.

        Args:
            action (str): Input action name.
            keys (pygame.key.ScancodeWrapper): Current keyboard state.
            context_dict (dict): Key-binding maps for a specific context.
        """
        if action not in context_dict:
            return False
        for key in context_dict[action]:
            if keys[key]:
                return True
        return False

    def get_normalized_move(self):
        """
        Get a normalized movement vector.

        Returns:
            pygame.Vector2: Normalized direction vector.
                Returns (0, 0) if no movement input is active.
        """
        # Return cached value if input unchanged
        if not self._normalized_dirty:
            return self._normalized_move

        # Recompute only when dirty
        if self.move.length_squared() > 0:
            self._normalized_move.update(self.move.normalize())
        else:
            self._normalized_move.update(0, 0)

        self._normalized_dirty = False
        return self._normalized_move

    # ===========================================================
    # System-Level Input (Global Hotkeys)
    # ===========================================================
    def handle_system_input(self, event, display, debug_hud):
        """
        Handle global system-level input that is always available.
        These bindings function independently of gameplay/ui contexts.

        Args:
            event (pygame.Event): The current input event.
            display (DisplayManager): Display manager for fullscreen toggle.
            debug_hud (DebugHUD): Debug HUD instance for toggling visibility.
        """
        if event.type != pygame.KEYDOWN:
            return

        keys = pygame.key.get_pressed()
        system_ctx = self.key_bindings.get("system", {})

        # -------------------------------------------------------
        # F11 → Toggle Fullscreen
        # -------------------------------------------------------
        if self._is_pressed_context("toggle_fullscreen", keys, system_ctx):
            display.toggle_fullscreen()
            DebugLogger.action("Toggled fullscreen via InputManager")

        # -------------------------------------------------------
        # F3 → Toggle Debug HUD (and sync hitbox visibility)
        # -------------------------------------------------------
        elif self._is_pressed_context("toggle_debug", keys, system_ctx):
            debug_hud.toggle()
            from src.core.runtime.game_settings import Debug
            Debug.HITBOX_VISIBLE = debug_hud.visible
            state = "Visible" if Debug.HITBOX_VISIBLE else "Hidden"
            DebugLogger.action(f"Hitbox rendering set → {state}")

    # ===========================================================
    # helper
    # ===========================================================

    def _build_key_caches(self):
        """Build flat {key: action} lookup for each context."""
        for context_name, actions in self.key_bindings.items():
            lookup = {}
            for action_name, keys in actions.items():
                for key in keys:
                    # Store action name for this key
                    lookup[key] = action_name
            self._key_to_action_cache[context_name] = lookup

    def _switch_active_cache(self, context_name):
        """Swap pointer to active lookup table + key list (zero-cost)."""
        self._active_lookup = self._key_to_action_cache.get(context_name, {})
        self._active_keys = self._context_keys.get(context_name, [])

    def _build_key_lists(self):
        """Pre-compute list of keys for each context (Phase 2)."""
        for context_name, actions in self.key_bindings.items():
            key_set = set()
            for keys in actions.values():
                key_set.update(keys)
            self._context_keys[context_name] = list(key_set)

    def _update_ui_controller(self):
        """Controller support for ui (only called if controller exists)."""
        hat_x, hat_y = self.controller.get_hat(0)
        x_axis = self.controller.get_axis(0)
        y_axis = self.controller.get_axis(1)
        threshold = 0.5

        if hat_y == 1 or y_axis < -threshold:
            self._actions["ui_up"]["pressed"] = True
        elif hat_y == -1 or y_axis > threshold:
            self._actions["ui_down"]["pressed"] = True
        if hat_x == -1 or x_axis < -threshold:
            self._actions["ui_left"]["pressed"] = True
        elif hat_x == 1 or x_axis > threshold:
            self._actions["ui_right"]["pressed"] = True

        self._actions["ui_confirm"]["pressed"] = self.controller.get_button(0)
        self._actions["ui_back"]["pressed"] = self.controller.get_button(1)

    # ===========================================================
    # Action Query Interface
    # ===========================================================
    def is_action_pressed(self, action: str) -> bool:
        """
        Check if an action was pressed this frame.

        Args:
            action (str): Action name (e.g., "attack", "bomb")

        Returns:
            bool: True if action is pressed this frame
        """
        return self._actions.get(action, {}).get("pressed", False)

    def is_action_held(self, action: str) -> bool:
        """
        Check if an action is currently held down.

        Args:
            action (str): Action name (e.g., "attack")

        Returns:
            bool: True if action is held
        """
        return self._actions.get(action, {}).get("held", False)

    # ===========================================================
    # Backward Compatibility Properties (temporary)
    # ===========================================================
    @property
    def attack_pressed(self) -> bool:
        return self.is_action_pressed("attack")

    @property
    def bomb_pressed(self) -> bool:
        return self.is_action_pressed("bomb")

    @property
    def pause_pressed(self) -> bool:
        return self.is_action_pressed("pause")

    @property
    def attack_held(self) -> bool:
        return self.is_action_held("attack")
