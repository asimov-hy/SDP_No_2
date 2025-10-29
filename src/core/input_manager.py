import pygame

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
    def __init__(self, key_bindings=None):
        # Key mapping
        self.key_bindings = key_bindings or DEFAULT_KEY_BINDINGS.copy()

        # Joystick setup (future support)
        pygame.joystick.init()
        self.controller = None
        if pygame.joystick.get_count() > 0:
            self.controller = pygame.joystick.Joystick(0)
            self.controller.init()

        # Movement state
        self.move = pygame.Vector2(0, 0)
        self._move_keyboard = pygame.Vector2(0, 0)
        self._move_controller = pygame.Vector2(0, 0)

        # Action states
        self.attack_pressed = False
        self.bomb_pressed = False
        self.pause_pressed = False

    def update(self):
        """Poll all input sources once per frame."""
        self._update_keyboard()
        self._update_controller()
        self._merge_inputs()

    def _update_keyboard(self):
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

        self.attack_pressed = self._is_pressed("attack", keys)
        self.bomb_pressed = self._is_pressed("bomb", keys)
        self.pause_pressed = self._is_pressed("pause", keys)

    def _update_controller(self):
        """Future placeholder: handles analog movement and buttons."""
        if not self.controller:
            self._move_controller.update(0, 0)
            return

        # Example layout (disabled until controller is connected)
        x_axis = self.controller.get_axis(0)
        y_axis = self.controller.get_axis(1)
        deadzone = 0.2
        self._move_controller.x = x_axis if abs(x_axis) > deadzone else 0
        self._move_controller.y = y_axis if abs(y_axis) > deadzone else 0

        # Future: map controller buttons to actions here

    def _merge_inputs(self):
        """Combine keyboard and controller input cleanly."""
        if self._move_controller.length_squared() > 0:
            self.move = self._move_controller
        else:
            self.move = self._move_keyboard

    def _is_pressed(self, action, keys):
        """Check if any bound key for an action is pressed."""
        if action not in self.key_bindings:
            return False
        for key in self.key_bindings[action]:
            if keys[key]:
                return True
        return False

    def get_normalized_move(self):
        """Return normalized vector (for consistent speed diagonally)."""
        if self.move.length_squared() > 0:
            return self.move.normalize()
        return pygame.Vector2(0, 0)
