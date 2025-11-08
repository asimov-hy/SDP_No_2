"""
player.py
---------
Defines the Player entity and its core update logic.

Responsibilities
----------------
- Maintain player position, movement, and health state.
- Handle shooting behavior via BulletManager.
- Update position based on input direction and delta time.
- Stay within screen boundaries.
- (Optional) Integrate with DebugLogger for movement and state tracking.
"""

import os
import json
import pygame

from src.core import settings
from src.core.settings import Display, Player as PlayerSettings, Layers
from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity


# ===========================================================
# Player Configuration Loader
# ===========================================================

DEFAULT_CONFIG = {
    "scale": 1.0,
    "speed": PlayerSettings.SPEED,   # Uses 300 from settings
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


# ===========================================================
# Player Entity Class
# ===========================================================

class Player(BaseEntity):
    """Represents the controllable player entity."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image):
        """
        Initialize the player with position, attributes, and image scaling.

        Args:
            x (float): Initial x-coordinate.
            y (float): Initial y-coordinate.
            image (pygame.Surface): Sprite surface for rendering.
        """
        cfg = PLAYER_CONFIG

        # -------------------------------------------------------
        # Apply scaling to sprite if specified
        # -------------------------------------------------------
        if cfg["scale"] != 1.0:
            w, h = image.get_size()
            image = pygame.transform.scale(image, (int(w * cfg["scale"]), int(h * cfg["scale"])))
            DebugLogger.state(f"Scaled sprite to {image.get_size()}")

        # Initialize base entity
        super().__init__(x, y, image)

        # -------------------------------------------------------
        # Player attributes
        # -------------------------------------------------------
        self.pos = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.speed = cfg["speed"]
        self.health = cfg["health"]
        self.invincible = cfg["invincible"]
        self.hitbox_scale = cfg["hitbox_scale"]

        # Collision setup
        self.hitbox = None
        self.has_hitbox = True

        # -------------------------------------------------------
        # Bullet / Shooting System
        # -------------------------------------------------------
        self.bullet_manager = None          # Assigned externally by GameScene
        self.shoot_cooldown = 0.1           # Seconds between shots
        self.shoot_timer = 0.0

        # Layer registration
        self.layer = Layers.PLAYER
        settings.GLOBAL_PLAYER = self

        DebugLogger.init(
            f"Initialized Player at ({x}, {y}) | Speed={self.speed} | HP={self.health}"
        )

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt):
        """
        Update player position, physics, and shooting each frame.

        Args:
            dt (float): Delta time.
        """
        if not self.alive:
            return

        move_vec = getattr(self, "move_vec", pygame.Vector2(0, 0))

        # -------------------------------------------------------
        # Tunable Physics Parameters
        # -------------------------------------------------------
        accel_rate = 3000     # Acceleration strength
        friction_rate = 500   # Friction strength (per-axis)
        max_speed = self.speed
        smooth_factor = 0.2   # Direction blending strength

        # -------------------------------------------------------
        # Apply Acceleration
        # -------------------------------------------------------
        if move_vec.length_squared() > 0:
            move_vec = move_vec.normalize()
            desired_velocity = move_vec * max_speed

            # Blend velocity toward desired direction
            self.velocity = self.velocity.lerp(desired_velocity, smooth_factor)

            # Gradual buildup of movement speed
            self.velocity += move_vec * accel_rate * dt
        else:
            # ---------------------------------------------------
            # Apply Friction (unified decay while maintaining direction)
            # ---------------------------------------------------
            current_speed = self.velocity.length()
            if current_speed > 0:
                new_speed = max(0.0, current_speed - friction_rate * dt)
                if new_speed < 5.0:
                    self.velocity.xy = (0, 0)
                else:
                    self.velocity.scale_to_length(new_speed)

        # -------------------------------------------------------
        # Apply final movement
        # -------------------------------------------------------
        self.pos += self.velocity * dt

        # -------------------------------------------------------
        # Clamp to screen boundaries
        # -------------------------------------------------------
        screen_width, screen_height = Display.WIDTH, Display.HEIGHT

        self.pos.x = max(0.0, min(self.pos.x, screen_width - self.rect.width))
        self.pos.y = max(0.0, min(self.pos.y, screen_height - self.rect.height))

        # Stop movement at edges to avoid wall sliding
        if self.pos.x <= 0 or self.pos.x >= screen_width - self.rect.width:
            self.velocity.x = 0
        if self.pos.y <= 0 or self.pos.y >= screen_height - self.rect.height:
            self.velocity.y = 0

        # Update render rect
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)

        # -------------------------------------------------------
        # Shooting Control
        # -------------------------------------------------------
        keys = pygame.key.get_pressed()
        self.shoot_timer += dt

        if keys[pygame.K_SPACE] and self.shoot_timer >= self.shoot_cooldown:
            self.shoot_timer = 0.0
            self.shoot()

        # -------------------------------------------------------
        # Hitbox Update
        # -------------------------------------------------------
        if self.hitbox:
            self.hitbox.update()

    # ===========================================================
    # Shooting Logic
    # ===========================================================
    def shoot(self):
        """Spawn bullets via the global BulletManager."""
        if not self.bullet_manager:
            DebugLogger.warn("Player attempted to shoot without BulletManager reference")
            return

        self.bullet_manager.spawn(
            pos=self.rect.center,
            vel=(0, -900),
            color=(255, 255, 100),
            radius=4,
            owner="player"
        )

    # ===========================================================
    # Collision Handling
    # ===========================================================
    def on_collision(self, other):
        """
        Handle collision interactions with other entities.
        Delegates bullet damage to the bullet itself via on_hit().
        Only handles direct collisions (e.g., Player <-> Enemy).
        """
        from src.entities.enemies.base_enemy import EnemyStraight

        # -------------------------------------------------------
        # Physical collisions with enemies (body-to-body)
        # -------------------------------------------------------
        if isinstance(other, EnemyStraight):
            if not self.invincible:
                self.take_damage(1, source=type(other).__name__)
                other.alive = False
                DebugLogger.state("[Collision] Player collided with Enemy!")
        else:
            DebugLogger.trace(f"[Collision] Unknown collision: {type(other).__name__}")

    # ===========================================================
    # Damage Handling
    # ===========================================================
    def take_damage(self, amount, source="unknown"):
        """
        Reduce player health when damaged.
        Handles death, logging, and invincibility checks.
        """
        if self.invincible:
            DebugLogger.trace(f"[DamageIgnored] Player invincible vs {source}")
            return

        self.health -= amount
        DebugLogger.state(f"[Damage] Player took {amount} from {source} → HP={self.health}")

        if self.health <= 0:
            self.alive = False
            DebugLogger.state("[Death] Player destroyed!")
