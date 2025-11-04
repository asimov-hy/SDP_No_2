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
from src.core.utils.debug_logger import DebugLogger

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
    }
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

        DebugLogger.init("║{:<59}║".format(f"\t[InputManager][INIT]\t→  Initialized"), show_meta=False)

        # Controller setup
        pygame.joystick.init()
        self.controller = None
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            DebugLogger.init("║{:<57}║".format(f"\t\t└─ [INIT]\t→  {self.controller.get_name()}"), show_meta=False)

        DebugLogger.init("║{:<57}║".format(f"\t\t└─ [INIT]\t→  Keyboard"), show_meta=False)

        # Movement and state tracking
        self.move = pygame.Vector2(0, 0)
        self._move_keyboard = pygame.Vector2(0, 0)
        self._move_controller = pygame.Vector2(0, 0)

        # Action states (gameplay)
        self.attack_pressed = False
        self.bomb_pressed = False
        self.pause_pressed = False

        # UI navigation states
        self.ui_up = False
        self.ui_down = False
        self.ui_left = False
        self.ui_right = False
        self.ui_confirm = False
        self.ui_back = False

    # ===========================================================
    # Context Management
    # ===========================================================
    def set_context(self, name: str):
        """
        Switch between contexts ("gameplay", "ui").
        """
        if name not in self.key_bindings:
            DebugLogger.warn(f"Unknown context: {name}")
            return
        self.context = name
        DebugLogger.state(f"Context switched to [{name.upper()}]")

    def get_context(self):
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
        keys = pygame.key.get_pressed()

        left = self._is_pressed("move_left", keys)
        right = self._is_pressed("move_right", keys)
        up = self._is_pressed("move_up", keys)
        down = self._is_pressed("move_down", keys)

        x = int(right) - int(left)
        y = int(down) - int(up)

        self._move_keyboard.update(x, y)

        # Actions
        self.attack_pressed = self._is_pressed("attack", keys)
        self.bomb_pressed = self._is_pressed("bomb", keys)
        self.pause_pressed = self._is_pressed("pause", keys)

        # Merge controller input (unchanged)
        self._update_controller()
        self._merge_inputs()

    # ===========================================================
    # UI Navigation Input
    # ===========================================================
    def _update_ui_navigation(self):
        keys = pygame.key.get_pressed()
        self.ui_up = self._is_pressed("navigate_up", keys)
        self.ui_down = self._is_pressed("navigate_down", keys)
        self.ui_left = self._is_pressed("navigate_left", keys)
        self.ui_right = self._is_pressed("navigate_right", keys)
        self.ui_confirm = self._is_pressed("confirm", keys)
        self.ui_back = self._is_pressed("back", keys)

        # ------------------------------------------
        # Controller support for UI
        # ------------------------------------------
        if self.controller:
            hat_x, hat_y = self.controller.get_hat(0)  # D-pad
            x_axis = self.controller.get_axis(0)  # Analog X
            y_axis = self.controller.get_axis(1)  # Analog Y
            threshold = 0.5

            # D-pad or analog emulate arrow keys
            if hat_y == 1 or y_axis < -threshold:
                self.ui_up = True
            elif hat_y == -1 or y_axis > threshold:
                self.ui_down = True

            if hat_x == -1 or x_axis < -threshold:
                self.ui_left = True
            elif hat_x == 1 or x_axis > threshold:
                self.ui_right = True

            # Controller buttons (customizable later)
            self.ui_confirm = self.controller.get_button(0)  # usually A / Cross
            self.ui_back = self.controller.get_button(1)  # usually B / Circle

    # ===========================================================
    # Controller Input
    # ===========================================================
    def _update_controller(self):
        """
        Poll analog stick axes and controller buttons.

        Notes:
            - Applies a deadzone to prevent drift.
            - Currently only supports primary analog movement.
        """
        if not self.controller:
            self._move_controller.update(0, 0)
            return

        x_axis = self.controller.get_axis(0)
        y_axis = self.controller.get_axis(1)
        deadzone = 0.2

        self._move_controller.x = x_axis if abs(x_axis) > deadzone else 0
        self._move_controller.y = y_axis if abs(y_axis) > deadzone else 0

    # ===========================================================
    # Input Merging and Query
    # ===========================================================
    def _merge_inputs(self):
        """Combine keyboard and controller input cleanly."""
        if self._move_controller.length_squared() > 0:
            self.move = self._move_controller
        else:
            self.move = self._move_keyboard

    def _is_pressed(self, action, keys):
        """
        Check if any bound key for an action is pressed.

        Args:
            action (str): Name of the input action.
            keys (pygame.key.ScancodeWrapper): Current keyboard state.

        Returns:
            bool: True if any key bound to the action is pressed.
        """
        ctx = self.key_bindings.get(self.context, {})
        if action not in ctx:
            return False
        for key in ctx[action]:
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
        if self.move.length_squared() > 0:
            return self.move.normalize()
        return pygame.Vector2(0, 0)