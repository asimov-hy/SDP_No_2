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

from src.core.settings import Display, Player as PlayerSettings, Layers
from src.core import settings
from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity

# ===========================================================
# Player Configuration Loader
# ===========================================================

DEFAULT_CONFIG = {
    "scale": 1.0,
    "speed": PlayerSettings.SPEED,  # Uses 300 from settings
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
            DebugLogger.system(f"Loaded config from {CONFIG_PATH}")
            return {**DEFAULT_CONFIG, **cfg}
    except Exception as e:
        DebugLogger.warn(f"Failed to load config: {e} — using defaults")
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
            DebugLogger.state(f"Scaled sprite to {image.get_size()}")

        super().__init__(x, y, image)

        # Player attributes
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.speed = cfg["speed"]
        self.health = cfg["health"]
        self.invincible = cfg["invincible"]
        self.hitbox_scale = cfg["hitbox_scale"]

        DebugLogger.init(f"Initialized at ({x}, {y}) | Speed={self.speed} | HP={self.health}")

        # -----------------------------------------------------------
        # Register this player globally (scene-independent)
        # -----------------------------------------------------------
        settings.GLOBAL_PLAYER = self

        self.layer = Layers.PLAYER

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt):
        """
        Update player position with velocity buildup and gradual slowdown.

        Args:
            dt (float): Delta time.
        """
        if not self.alive:
            return

        move_vec = getattr(self, "move_vec", pygame.Vector2(0, 0))

        # ==========================================================
        # Tunable Physics Parameters
        # ==========================================================
        accel_rate = 3000  # Acceleration strength
        friction_rate = 500  # Friction strength (per-axis)
        max_speed = self.speed
        smooth_factor = 0.2  # How smoothly direction turns

        # ==========================================================
        # Apply Acceleration
        # ==========================================================
        if move_vec.length_squared() > 0:
            # Normalize for consistent diagonal speed
            move_vec = move_vec.normalize()

            # Smoothly blend velocity toward the desired direction
            desired_velocity = move_vec * max_speed
            self.velocity = self.velocity.lerp(desired_velocity, smooth_factor)

            # Apply additive acceleration for gradual buildup
            self.velocity += move_vec * accel_rate * dt

        else:
            # ======================================================
            # Apply Unified Friction (preserves direction)
            # ======================================================
            current_speed = self.velocity.length()
            if current_speed > 0:
                # Reduce speed while maintaining direction
                new_speed = max(0.0, current_speed - friction_rate * dt)

                if new_speed < 5:  # Stop near zero
                    self.velocity.x = 0
                    self.velocity.y = 0
                else:
                    self.velocity.scale_to_length(new_speed)

        # ==========================================================
        # Apply final movement
        # ==========================================================
        self.pos += self.velocity * dt

        # ==========================================================
        # Clamp to screen boundaries
        # ==========================================================
        screen_width = Display.WIDTH
        screen_height = Display.HEIGHT

        # Clamp position
        self.pos.x = max(0.0, min(self.pos.x, screen_width - self.rect.width))
        self.pos.y = max(0.0, min(self.pos.y, screen_height - self.rect.height))

        # Stop velocity when hitting walls (prevents "pushing" against boundaries)
        if self.pos.x <= 0 or self.pos.x >= screen_width - self.rect.width:
            self.velocity.x = 0
        if self.pos.y <= 0 or self.pos.y >= screen_height - self.rect.height:
            self.velocity.y = 0

        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)