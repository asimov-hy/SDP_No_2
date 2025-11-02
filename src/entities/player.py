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

from src.core.settings import PLAYER_SPEED, SCREEN_WIDTH, SCREEN_HEIGHT
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

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt, move_vec):
        """
        Update player position based on input vector and time delta.

        Args:
            dt (float): Time elapsed since last frame.
            move_vec (pygame.Vector2): Normalized movement direction.
        """
        if not self.alive:
            return

        if move_vec.length_squared() > 0:
            self.velocity = move_vec * self.speed * dt
            self.rect.x += self.velocity.x
            self.rect.y += self.velocity.y
        else:
            self.velocity.update(0, 0)

        # Keep player inside screen bounds
        self.rect.clamp_ip(pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))