"""
input_manager.py
----------------
Unified input system with context-aware action queries.

Provides:
- Context-based input handling (gameplay, ui, system)
- Edge detection (pressed, held, released)
- Keyboard and controller support
- Normalized movement vectors
"""

import pygame

from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Debug, Input


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
    "system": {
        "toggle_debug": [pygame.K_F3],
        "toggle_fullscreen": [pygame.K_F11],
    },
}


class InputManager:
    """
    Unified input system with context-aware action queries.

    Supports keyboard and controller input with automatic edge detection
    for pressed/held/released states.

    Usage:
        if input_manager.action_pressed("attack"):   # Rising edge
            player.shoot()

        if input_manager.action_held("attack"):      # Continuous
            player.charge_shot()

        if input_manager.action_released("attack"):  # Falling edge
            player.fire_charged_shot()

        move_dir = input_manager.get_normalized_move()  # Movement vector
    """

    # ===========================================================
    # Initialization
    # ===========================================================

    def __init__(self, key_bindings=None, display_manager=None):
        """
        Initialize input system.

        Args:
            key_bindings: Custom key bindings dict (uses DEFAULT_KEY_BINDINGS if None)
            display_manager: Reference for mouse coordinate conversion
        """
        DebugLogger.init_entry("InputManager")

        self.key_bindings = key_bindings or DEFAULT_KEY_BINDINGS
        self.display_manager = display_manager
        self.context = "gameplay"

        # Build lookup tables
        self._init_lookup_tables()
        self._init_action_registry()
        self._init_movement_state()
        self._init_controller()

        # Cursor auto-hide system
        self.mouse_enabled = True
        self.prev_mouse_pos = pygame.mouse.get_pos()
        self.mouse_move_threshold = 5

        self._validate_bindings()

    def _init_lookup_tables(self):
        """Build bidirectional lookup tables for fast key/action queries."""
        self._key_to_action_cache = {}
        self._action_to_keys_cache = {}
        self._context_keys = {}

        for context_name, actions in self.key_bindings.items():
            key_to_action = {}
            action_to_keys = {}
            key_set = set()

            for action_name, keys in actions.items():
                key_set.update(keys)
                action_to_keys[action_name] = tuple(keys)
                for key in keys:
                    key_to_action[key] = action_name

            self._key_to_action_cache[context_name] = key_to_action
            self._action_to_keys_cache[context_name] = action_to_keys
            self._context_keys[context_name] = tuple(key_set)

        # Set initial active context
        self._active_lookup = self._key_to_action_cache["gameplay"]
        self._active_action_to_keys = self._action_to_keys_cache["gameplay"]
        self._active_keys = self._context_keys["gameplay"]

    def _init_action_registry(self):
        """Initialize state tracking for all non-system actions."""
        self._actions = {}

        for context_name, actions in self.key_bindings.items():
            if context_name == "system":
                continue

            for action_name in actions:
                self._actions[action_name] = {
                    "pressed": False,
                    "held": False,
                    "released": False,
                    "prev_held": False,
                }

    def _init_movement_state(self):
        """Initialize movement vector tracking."""
        self.move = pygame.Vector2(0, 0)
        self._move_keyboard = pygame.Vector2(0, 0)
        self._move_controller = pygame.Vector2(0, 0)
        self._normalized_move = pygame.Vector2(0, 0)
        self._last_raw_move = pygame.Vector2(0, 0)
        self._normalized_dirty = True

    def _init_controller(self):
        """Initialize game controller if available."""
        pygame.joystick.init()
        self.controller = None

        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            DebugLogger.init_sub(f"Controller: {self.controller.get_name()}")

    def _validate_bindings(self):
        """Warn if system keys overlap with gameplay/ui contexts."""
        system_keys = set()
        for keys in self.key_bindings["system"].values():
            system_keys.update(keys)

        other_keys = set()
        for ctx in ("gameplay", "ui"):
            for keys in self.key_bindings[ctx].values():
                other_keys.update(keys)

        overlap = system_keys & other_keys
        if overlap:
            DebugLogger.warn(f"Overlapping system keys: {overlap}")

    # ===========================================================
    # Context Management
    # ===========================================================

    def set_context(self, name: str):
        """
        Switch input context.

        Syncs held state to prevent false edges on context switch.

        Args:
            name: Context name ("gameplay", "ui", "system")
        """
        if name not in self.key_bindings:
            DebugLogger.warn(f"Unknown context: {name}")
            return

        self.context = name
        self._active_lookup = self._key_to_action_cache[name]
        self._active_action_to_keys = self._action_to_keys_cache[name]
        self._active_keys = self._context_keys[name]

        # Sync action states to prevent false edges
        self._sync_action_states_on_context_switch()

        DebugLogger.state(f"Context switched to [{name.upper()}]")

    def _sync_action_states_on_context_switch(self):
        """Reset edge states and sync held state to current key state."""
        keys = pygame.key.get_pressed()

        for action_name, state in self._actions.items():
            state["pressed"] = False
            state["released"] = False

            if action_name in self._active_action_to_keys:
                is_held = self._is_action_pressed(action_name, keys)
                state["prev_held"] = is_held
                state["held"] = is_held
            else:
                state["prev_held"] = False
                state["held"] = False

    # ===========================================================
    # Public API: Action Queries
    # ===========================================================

    def action_pressed(self, action: str) -> bool:
        """
        Check if action was just pressed this frame (rising edge).

        Use for single-shot actions: shooting, jumping, menu confirm.
        """
        state = self._actions.get(action)
        return state["pressed"] if state else False

    def action_held(self, action: str) -> bool:
        """
        Check if action is currently held down.

        Use for continuous actions: charging, sprinting.
        """
        state = self._actions.get(action)
        return state["held"] if state else False

    def action_released(self, action: str) -> bool:
        """
        Check if action was just released this frame (falling edge).

        Use for release triggers: charge releases, toggle completion.
        """
        state = self._actions.get(action)
        return state["released"] if state else False

    def get_normalized_move(self) -> pygame.Vector2:
        """
        Get normalized movement vector (gameplay context only).

        Returns unit vector for consistent diagonal movement speed.
        """
        if self._normalized_dirty:
            if self.move.length_squared() > 0:
                self._normalized_move.update(self.move.normalize())
            else:
                self._normalized_move.update(0, 0)
            self._normalized_dirty = False

        return self._normalized_move

    def get_mouse_pos(self) -> tuple:
        """
        Get current mouse position in game coordinates.

        Returns:
            (x, y) tuple in game space (accounts for display scaling)
        """
        screen_pos = pygame.mouse.get_pos()
        if self.display_manager:
            return self.display_manager.screen_to_game_pos(*screen_pos)
        return screen_pos

    # ===========================================================
    # Frame Update
    # ===========================================================

    def update(self):
        """Poll all input sources. Call once per frame."""
        keys = pygame.key.get_pressed()

        # Auto-hide cursor based on input device
        self._update_cursor_visibility(keys)

        if self.context == "gameplay":
            self._update_gameplay(keys)
        elif self.context == "ui":
            self._update_ui(keys)

    def _update_gameplay(self, keys):
        """Update gameplay input: movement and actions."""
        self._update_movement(keys)
        self._update_action_state("attack", keys)
        self._update_action_state("bomb", keys)
        self._update_action_state("pause", keys)

    def _update_ui(self, keys):
        """Update UI input: navigation and selection."""
        self._update_action_state("navigate_up", keys)
        self._update_action_state("navigate_down", keys)
        self._update_action_state("navigate_left", keys)
        self._update_action_state("navigate_right", keys)
        self._update_action_state("confirm", keys)
        self._update_action_state("back", keys)

        if self.controller:
            self._merge_controller_ui()

    def _update_movement(self, keys):
        """Update movement vector from keyboard and controller."""
        # Keyboard input
        left = self._is_action_pressed("move_left", keys)
        right = self._is_action_pressed("move_right", keys)
        up = self._is_action_pressed("move_up", keys)
        down = self._is_action_pressed("move_down", keys)

        self._move_keyboard.update(int(right) - int(left), int(down) - int(up))

        # Merge with controller
        if self.controller:
            self._merge_controller_movement()
        else:
            self.move.update(self._move_keyboard)

        # Track changes for normalization cache
        if self.move != self._last_raw_move:
            self._normalized_dirty = True
            self._last_raw_move.update(self.move)

    def _update_action_state(self, action: str, keys):
        """
        Update action state with edge detection.

        Compares current frame to previous frame to detect:
        - pressed: False → True (rising edge)
        - released: True → False (falling edge)
        - held: current state
        """
        state = self._actions[action]
        current_held = self._is_action_pressed(action, keys)
        prev_held = state["prev_held"]

        state["pressed"] = current_held and not prev_held
        state["released"] = not current_held and prev_held
        state["held"] = current_held
        state["prev_held"] = current_held

    # ===========================================================
    # Controller Integration
    # ===========================================================

    def _merge_controller_movement(self):
        """Merge controller analog stick with keyboard movement."""
        x_axis = self.controller.get_axis(0)
        y_axis = self.controller.get_axis(1)
        deadzone = Input.CONTROLLER_DEADZONE

        self._move_controller.x = x_axis if abs(x_axis) > deadzone else 0
        self._move_controller.y = y_axis if abs(y_axis) > deadzone else 0

        # Controller overrides keyboard when active
        if self._move_controller.length_squared() > 0:
            self.move.update(self._move_controller)
        else:
            self.move.update(self._move_keyboard)

    def _merge_controller_ui(self):
        """Merge controller input for UI navigation."""
        hat_x, hat_y = (0, 0)
        if self.controller.get_numhats() > 0:
            hat_x, hat_y = self.controller.get_hat(0)

        x_axis = self.controller.get_axis(0)
        y_axis = self.controller.get_axis(1)
        threshold = Input.CONTROLLER_UI_THRESHOLD

        # Map controller inputs to UI actions
        controller_mappings = [
            (hat_y == 1 or y_axis < -threshold, "navigate_up"),
            (hat_y == -1 or y_axis > threshold, "navigate_down"),
            (hat_x == -1 or x_axis < -threshold, "navigate_left"),
            (hat_x == 1 or x_axis > threshold, "navigate_right"),
            (self.controller.get_button(0), "confirm"),
            (self.controller.get_button(1), "back"),
        ]

        for is_active, action in controller_mappings:
            if is_active:
                self._set_controller_action(action)

    def _set_controller_action(self, action: str):
        """Set action state from controller input with edge detection."""
        state = self._actions[action]
        if not state["prev_held"]:
            state["pressed"] = True
        state["held"] = True

    def _update_cursor_visibility(self, keys):
        """Toggle mouse_enabled based on input device used."""
        current_mouse_pos = pygame.mouse.get_pos()
        mouse_delta = (
            abs(current_mouse_pos[0] - self.prev_mouse_pos[0]),
            abs(current_mouse_pos[1] - self.prev_mouse_pos[1])
        )

        # Mouse moved significantly -> enable mouse
        if mouse_delta[0] > self.mouse_move_threshold or mouse_delta[1] > self.mouse_move_threshold:
            if not self.mouse_enabled:
                self.mouse_enabled = True
                pygame.mouse.set_visible(True)
            self.prev_mouse_pos = current_mouse_pos
            return

        self.prev_mouse_pos = current_mouse_pos

        # Keyboard used -> disable mouse
        if any(keys):
            self._disable_mouse()
            return

        # Controller used -> disable mouse
        if self.controller:
            for btn in range(self.controller.get_numbuttons()):
                if self.controller.get_button(btn):
                    self._disable_mouse()
                    return
            for axis in range(self.controller.get_numaxes()):
                if abs(self.controller.get_axis(axis)) > Input.CONTROLLER_DEADZONE:
                    self._disable_mouse()
                    return
            if self.controller.get_numhats() > 0 and self.controller.get_hat(0) != (0, 0):
                self._disable_mouse()
                return

    def get_effective_mouse_pos(self):
        """
        Get mouse position, or off-screen if mouse is disabled.

        Returns:
            tuple: Mouse position or (-1, -1) if mouse disabled
        """
        if not self.mouse_enabled:
            return (-1, -1)

        screen_pos = pygame.mouse.get_pos()
        if self.display_manager:
            return self.display_manager.screen_to_game_pos(*screen_pos)
        return screen_pos

    def _disable_mouse(self):
        """Disable mouse input mode."""
        if self.mouse_enabled:
            self.mouse_enabled = False
            pygame.mouse.set_visible(False)

    # ===========================================================
    # System Input (Global Hotkeys)
    # ===========================================================

    def handle_system_input(self, event, display, debug_hud):
        """
        Handle global hotkeys independent of context.

        Args:
            event: pygame event to process
            display: DisplayManager for fullscreen toggle
            debug_hud: DebugHUD for visibility toggle
        """
        if event.type != pygame.KEYDOWN:
            return

        system_bindings = self.key_bindings.get("system", {})

        if self._is_system_key_pressed("toggle_fullscreen", event.key, system_bindings):
            display.toggle_fullscreen()
            DebugLogger.action("Toggled fullscreen")

        elif self._is_system_key_pressed("toggle_debug", event.key, system_bindings):
            debug_hud.toggle()
            Debug.HITBOX_VISIBLE = debug_hud.visible
            DebugLogger.action(f"Debug HUD: {'ON' if debug_hud.visible else 'OFF'}")

    def _is_system_key_pressed(self, action: str, key: int, bindings: dict) -> bool:
        """Check if key matches a system action binding."""
        return key in bindings.get(action, ())

    # ===========================================================
    # Internal Helpers
    # ===========================================================

    def _is_action_pressed(self, action: str, keys) -> bool:
        """Check if any key bound to action is currently pressed. O(1) lookup."""
        bound_keys = self._active_action_to_keys.get(action, ())
        for key in bound_keys:
            if keys[key]:
                return True
        return False