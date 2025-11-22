"""
input_manager.py
----------------
Unified input system with context-aware action queries.
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
    "system": {
        "toggle_debug": [pygame.K_F3],
        "toggle_fullscreen": [pygame.K_F11],
    },
}


class InputManager:
    """
    Unified input system with context-aware action queries.

    Usage:
        # Single press (rising edge)
        if input_manager.action_pressed("attack"):
            player.shoot()

        # Hold (continuous)
        if input_manager.action_held("attack"):
            player.charge_shot()

        # Release (falling edge)
        if input_manager.action_released("attack"):
            player.fire_charged_shot()

        # Movement (gameplay only)
        move_dir = input_manager.get_normalized_move()
    """

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, key_bindings=None):
        """Initialize input system with optional custom bindings."""
        self.key_bindings = key_bindings or DEFAULT_KEY_BINDINGS
        self.context = "gameplay"

        # Build lookup tables
        self._key_to_action_cache = {}
        self._context_keys = {}
        self._build_lookup_tables()

        # Active context cache
        self._active_lookup = self._key_to_action_cache["gameplay"]
        self._active_keys = self._context_keys["gameplay"]

        DebugLogger.init_entry("InputManager")
        self._validate_bindings()

        # Controller setup
        pygame.joystick.init()
        self.controller = None
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            DebugLogger.init_sub(f"Controller: {self.controller.get_name()}")

        # Movement state (gameplay only)
        self.move = pygame.Vector2(0, 0)
        self._move_keyboard = pygame.Vector2(0, 0)
        self._move_controller = pygame.Vector2(0, 0)
        self._normalized_move = pygame.Vector2(0, 0)
        self._last_raw_move = pygame.Vector2(0, 0)
        self._normalized_dirty = True

        # Action state registry
        self._actions = {}
        self._init_action_registry()

    def _build_lookup_tables(self):
        """Build key→action lookup tables for fast queries."""
        for context_name, actions in self.key_bindings.items():
            lookup = {}
            key_set = set()

            for action_name, keys in actions.items():
                key_set.update(keys)
                for key in keys:
                    lookup[key] = action_name

            self._key_to_action_cache[context_name] = lookup
            self._context_keys[context_name] = list(key_set)

    def _init_action_registry(self):
        """Auto-register all actions from bindings."""
        for context_name, actions in self.key_bindings.items():
            if context_name == "system":  # Skip system actions
                continue

            for action_name in actions.keys():
                self._actions[action_name] = {
                    "pressed": False,
                    "held": False,
                    "released": False,
                    "prev_held": False
                }

    def _validate_bindings(self):
        """Warn if system keys overlap with gameplay/ui."""
        system_keys = {k for keys in self.key_bindings["system"].values() for k in keys}
        other_keys = {k for ctx in ("gameplay", "ui")
                      for keys in self.key_bindings[ctx].values() for k in keys}
        overlap = system_keys & other_keys
        if overlap:
            DebugLogger.warn(f"Overlapping system keys: {overlap}")

    # ===========================================================
    # Context Management
    # ===========================================================
    def set_context(self, name: str):
        """Switch input context (called by SceneManager)."""
        if name not in self.key_bindings:
            DebugLogger.warn(f"Unknown context: {name}")
            return

        self.context = name
        self._active_lookup = self._key_to_action_cache[name]
        self._active_keys = self._context_keys[name]

        # Reset edge states AND sync prev_held to current key state
        # This prevents false rising edges when switching contexts
        keys = pygame.key.get_pressed()
        for action_name, action_state in self._actions.items():
            action_state["pressed"] = False
            action_state["released"] = False
            # Only sync held state if action exists in new context
            if action_name in self._active_lookup.values():
                is_currently_held = self._is_pressed(action_name, keys)
                action_state["prev_held"] = is_currently_held
                action_state["held"] = is_currently_held
            else:
                # Action doesn't exist in new context - reset completely
                action_state["prev_held"] = False
                action_state["held"] = False

        DebugLogger.state(f"Context switched to [{name.upper()}]")

    # ===========================================================
    # Public Action Query API
    # ===========================================================
    def action_pressed(self, action: str) -> bool:
        """
        Check if action was just pressed this frame (rising edge).

        Use for: Single-shot actions like shooting, jumping, menu confirm.

        Args:
            action: Action name from current context bindings

        Returns:
            True only on the frame the key was pushed down
        """
        return self._actions.get(action, {}).get("pressed", False)

    def action_held(self, action: str) -> bool:
        """
        Check if action is currently held down.

        Use for: Continuous actions like charging, sprinting.

        Args:
            action: Action name from current context bindings

        Returns:
            True every frame while key is down
        """
        return self._actions.get(action, {}).get("held", False)

    def action_released(self, action: str) -> bool:
        """
        Check if action was just released this frame (falling edge).

        Use for: Charge releases, focus mode toggles.

        Args:
            action: Action name from current context bindings

        Returns:
            True only on the frame the key was released
        """
        return self._actions.get(action, {}).get("released", False)

    def get_normalized_move(self) -> pygame.Vector2:
        """
        Get normalized movement vector (gameplay context only).

        Ensures consistent movement speed in all directions.

        Returns:
            Normalized direction vector or (0, 0)
        """
        if not self._normalized_dirty:
            return self._normalized_move

        if self.move.length_squared() > 0:
            self._normalized_move.update(self.move.normalize())
        else:
            self._normalized_move.update(0, 0)

        self._normalized_dirty = False
        return self._normalized_move

    # ===========================================================
    # Frame Update (called by game loop)
    # ===========================================================
    def update(self):
        """Poll all input sources once per frame."""
        keys = pygame.key.get_pressed()

        if self.context == "gameplay":
            self._update_gameplay(keys)
        elif self.context == "ui":
            self._update_ui(keys)

    def _update_gameplay(self, keys):
        """Update gameplay input state with edge detection."""
        # Movement
        left = self._is_pressed("move_left", keys)
        right = self._is_pressed("move_right", keys)
        up = self._is_pressed("move_up", keys)
        down = self._is_pressed("move_down", keys)

        x = int(right) - int(left)
        y = int(down) - int(up)
        self._move_keyboard.update(x, y)

        # Merge controller if available
        if self.controller:
            self._merge_controller_movement()
        else:
            self.move.update(self._move_keyboard)

        # Track movement changes
        if self.move != self._last_raw_move:
            self._normalized_dirty = True
            self._last_raw_move.update(self.move)

        # Update actions with edge detection
        self._update_action_state("attack", keys)
        self._update_action_state("bomb", keys)
        self._update_action_state("pause", keys)

    def _update_ui(self, keys):
        """Update UI navigation input state with edge detection."""
        self._update_action_state("navigate_up", keys)
        self._update_action_state("navigate_down", keys)
        self._update_action_state("navigate_left", keys)
        self._update_action_state("navigate_right", keys)
        self._update_action_state("confirm", keys)
        self._update_action_state("back", keys)

        # Controller support for UI
        if self.controller:
            self._merge_controller_ui()

    def _update_action_state(self, action: str, keys):
        """
        Update action state with edge detection.

        Detects:
        - pressed: rising edge (just pushed)
        - held: current state
        - released: falling edge (just released)
        """
        current_held = self._is_pressed(action, keys)
        prev_held = self._actions[action]["prev_held"]

        self._actions[action]["pressed"] = current_held and not prev_held
        self._actions[action]["released"] = not current_held and prev_held
        self._actions[action]["held"] = current_held
        self._actions[action]["prev_held"] = current_held

    def _merge_controller_movement(self):
        """Merge controller axes with keyboard movement."""
        x_axis = self.controller.get_axis(0)
        y_axis = self.controller.get_axis(1)
        deadzone = 0.2

        self._move_controller.x = x_axis if abs(x_axis) > deadzone else 0
        self._move_controller.y = y_axis if abs(y_axis) > deadzone else 0

        # Controller overrides keyboard
        if self._move_controller.length_squared() > 0:
            self.move.update(self._move_controller)
        else:
            self.move.update(self._move_keyboard)

    def _merge_controller_ui(self):
        """Merge controller input for UI navigation (additive with keyboard)."""
        if self.controller.get_numhats() > 0:
            hat_x, hat_y = self.controller.get_hat(0)
        else:
            hat_x, hat_y = 0, 0

        x_axis = self.controller.get_axis(0)
        y_axis = self.controller.get_axis(1)
        threshold = 0.5

        # D-pad or stick up
        if hat_y == 1 or y_axis < -threshold:
            if not self._actions["navigate_up"]["prev_held"]:
                self._actions["navigate_up"]["pressed"] = True
            self._actions["navigate_up"]["held"] = True

        # D-pad or stick down
        if hat_y == -1 or y_axis > threshold:
            if not self._actions["navigate_down"]["prev_held"]:
                self._actions["navigate_down"]["pressed"] = True
            self._actions["navigate_down"]["held"] = True

        # D-pad or stick left
        if hat_x == -1 or x_axis < -threshold:
            if not self._actions["navigate_left"]["prev_held"]:
                self._actions["navigate_left"]["pressed"] = True
            self._actions["navigate_left"]["held"] = True

        # D-pad or stick right
        if hat_x == 1 or x_axis > threshold:
            if not self._actions["navigate_right"]["prev_held"]:
                self._actions["navigate_right"]["pressed"] = True
            self._actions["navigate_right"]["held"] = True

        # Buttons
        if self.controller.get_button(0):
            if not self._actions["confirm"]["prev_held"]:
                self._actions["confirm"]["pressed"] = True
            self._actions["confirm"]["held"] = True

        if self.controller.get_button(1):
            if not self._actions["back"]["prev_held"]:
                self._actions["back"]["pressed"] = True
            self._actions["back"]["held"] = True

    def _is_pressed(self, action: str, keys) -> bool:
        """Check if any key bound to action is pressed."""
        for key in self._active_keys:
            if keys[key] and self._active_lookup.get(key) == action:
                return True
        return False

    # ===========================================================
    # System-Level Input (Global Hotkeys)
    # ===========================================================
    def handle_system_input(self, event, display, debug_hud):
        """Handle global hotkeys (F3, F11) independent of context."""
        if event.type != pygame.KEYDOWN:
            return

        keys = pygame.key.get_pressed()
        system_ctx = self.key_bindings.get("system", {})

        # F11 - Fullscreen
        if self._is_pressed_in_context("toggle_fullscreen", keys, system_ctx):
            display.toggle_fullscreen()
            DebugLogger.action("Toggled fullscreen")

        # F3 - Debug HUD
        elif self._is_pressed_in_context("toggle_debug", keys, system_ctx):
            debug_hud.toggle()
            from src.core.runtime.game_settings import Debug
            Debug.HITBOX_VISIBLE = debug_hud.visible
            DebugLogger.action(f"Debug HUD: {'ON' if debug_hud.visible else 'OFF'}")

    def _is_pressed_in_context(self, action: str, keys, context_dict: dict) -> bool:
        """Check if action is pressed in specific context dict."""
        if action not in context_dict:
            return False
        return any(keys[key] for key in context_dict[action])

    def get_mouse_pos(self):
        """
        Get current mouse position.

        Returns:
            Tuple[int, int]: (x, y) mouse coordinates
        """
        return pygame.mouse.get_pos()