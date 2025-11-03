"""
player.py
---------
Defines the Player entity and its core update logic.

Responsibilities
----------------
- Maintain player position, movement, and health state.
- Update position based on input direction and delta time.
- Stay within screen boundaries.
- (Optional) Integrate with DebugLogger for movement and state tracking.
"""
import pygame
import json
import os

from src.core import settings
from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity

# ===========================================================
# Player Configuration Loader
# ===========================================================

DEFAULT_CONFIG = {
    "scale": 1.0,
    "speed": 300,
    "health": 3,
    "invincible": False,
    "hitbox_scale": 0.85
}

CONFIG_PATH = os.path.join("src", "data", "player_config.json")

def load_player_config():
    """Load player configuration from JSON file or fallback to defaults."""
    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
            DebugLogger.system("Player", f"Loaded config from {CONFIG_PATH}")
            return {**DEFAULT_CONFIG, **cfg}
    except Exception as e:
        DebugLogger.warn("Player", f"Failed to load config: {e} — using defaults")
        return DEFAULT_CONFIG

PLAYER_CONFIG = load_player_config()

class Player(BaseEntity):
    """Represents the controllable player entity."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image):
        """
        Initialize the player with position and sprite.

        Args:
            x (float): Initial x-coordinate.
            y (float): Initial y-coordinate.
            image (pygame.Surface): The sprite surface for rendering.
        """
        cfg = PLAYER_CONFIG

        # Apply scale to image
        if cfg["scale"] != 1.0:
            w, h = image.get_size()
            image = pygame.transform.scale(image, (int(w * cfg["scale"]), int(h * cfg["scale"])))
            DebugLogger.state("Player", f"Scaled sprite to {image.get_size()}")

        super().__init__(x, y, image)

        # Player attributes
        self.velocity = pygame.Vector2(0, 0)
        self.speed = cfg["speed"]
        self.health = cfg["health"]
        self.invincible = cfg["invincible"]
        self.hitbox_scale = cfg["hitbox_scale"]

        DebugLogger.init("Player", f"Initialized at ({x}, {y}) | Speed={self.speed} | HP={self.health}")

        # -----------------------------------------------------------
        # Register this player globally (scene-independent)
        # -----------------------------------------------------------
        settings.GLOBAL_PLAYER = self

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt, move_vec):
        """
        Update player position with velocity buildup and gradual slowdown.

        Args:
            dt (float): Delta time.
            move_vec (pygame.Vector2): Normalized input direction vector.
        """
        if not self.alive:
            return

        # ==========================================================
        # Tunable Physics Parameters
        # ==========================================================
        accel_rate = 3000  # How fast player accelerates toward max speed
        friction_rate = 500  # How quickly the player slows when not pressing keys
        max_speed = self.speed  # The maximum movement speed

        # ==========================================================
        # Apply Acceleration (when moving)
        # ==========================================================
        if move_vec.length_squared() > 0:
            # Accelerate in direction of input
            target_velocity = move_vec * max_speed
            to_target = target_velocity - self.velocity

            # Limit acceleration for smoothness
            if to_target.length() > accel_rate * dt:
                to_target.scale_to_length(accel_rate * dt)

            # Apply acceleration
            self.velocity += to_target
        else:
            # ======================================================
            # Apply Friction (when no input)
            # ======================================================
            speed = self.velocity.length()
            if speed > 0:
                decel = friction_rate * dt
                # Gradually reduce speed
                if decel >= speed:
                    self.velocity.update(0, 0)
                else:
                    self.velocity.scale_to_length(speed - decel)

        # ==========================================================
        # Cap Velocity to Max Speed
        # ==========================================================
        if self.velocity.length() > max_speed:
            self.velocity.scale_to_length(max_speed)

        # ==========================================================
        # Update Position and Clamp
        # ==========================================================
        self.rect.x += self.velocity.x * dt
        self.rect.y += self.velocity.y * dt
        self.rect.clamp_ip(pygame.Rect(0, 0, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))