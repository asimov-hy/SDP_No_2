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

# Default key bindings (easily replaceable later)
DEFAULT_KEY_BINDINGS = {
    "move_left": [pygame.K_LEFT, pygame.K_a],
    "move_right": [pygame.K_RIGHT, pygame.K_d],
    "move_up": [pygame.K_UP, pygame.K_w],
    "move_down": [pygame.K_DOWN, pygame.K_s],
    "attack": [pygame.K_SPACE],
    "bomb": [pygame.K_LSHIFT, pygame.K_RSHIFT],
    "pause": [pygame.K_ESCAPE],
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
        self.key_bindings = key_bindings or DEFAULT_KEY_BINDINGS.copy()

        # Controller setup
        pygame.joystick.init()
        self.controller = None
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()
            DebugLogger.init("", "║{:<62}║".format(f"\t[InputManager][INIT]\t→  Controller: {self.controller.get_name()}"))
        else:
            DebugLogger.init("", "║{:<59}║".format(f"\t[InputManager][INIT]\t→  Keyboard"))

        # Movement and state tracking
        self.move = pygame.Vector2(0, 0)
        self._move_keyboard = pygame.Vector2(0, 0)
        self._move_controller = pygame.Vector2(0, 0)

        # Action states
        self.attack_pressed = False
        self.bomb_pressed = False
        self.pause_pressed = False

    # ===========================================================
    # Update Cycle
    # ===========================================================
    def update(self):
        """Poll all input sources once per frame."""
        self._update_keyboard()
        self._update_controller()
        self._merge_inputs()

    # ===========================================================
    # Keyboard Input
    # ===========================================================
    def _update_keyboard(self):
        """
        Read movement and action keys from the keyboard.

        Sets movement and action states according to the active bindings.
        """
        keys = pygame.key.get_pressed()
        self._move_keyboard.update(0, 0)

        if self._is_pressed("move_left", keys):
            self._move_keyboard.x -= 1
        if self._is_pressed("move_right", keys):
            self._move_keyboard.x += 1
        if self._is_pressed("move_up", keys):
            self._move_keyboard.y -= 1
        if self._is_pressed("move_down", keys):
            self._move_keyboard.y += 1

        # Actions
        self.attack_pressed = self._is_pressed("attack", keys)
        self.bomb_pressed = self._is_pressed("bomb", keys)
        self.pause_pressed = self._is_pressed("pause", keys)

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
        if action not in self.key_bindings:
            return False
        for key in self.key_bindings[action]:
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
