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
- Integrate with DebugLogger for movement and state tracking.
"""

import pygame
from src.core.game_settings import Display, Player as PlayerSettings, Layers
from src.core.game_state import STATE
from src.core.utils.debug_logger import DebugLogger
from src.core.utils.config_manager import load_json
from src.entities.base_entity import BaseEntity
from src.systems.combat.collision_hitbox import CollisionHitbox

# ===========================================================
# Player Configuration Loader
# ===========================================================

DEFAULT_CONFIG = {
    "scale": 1.0,
    "speed": PlayerSettings.SPEED,   # Uses 300 from settings
    "health": 3,
    "invincible": False,
    "hitbox_scale": 0.85,
}

PLAYER_CONFIG = load_json("player_config.json", DEFAULT_CONFIG)


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
            new_size = (int(w * cfg["scale"]), int(h * cfg["scale"]))
            image = pygame.transform.scale(image, new_size)
            DebugLogger.state(f"[Player] Sprite scaled to {new_size}")

        # Initialize base entity
        super().__init__(x, y, image)

        # -------------------------------------------------------
        # Core attributes
        # -------------------------------------------------------
        self.velocity = pygame.Vector2(0, 0)
        self.speed = cfg["speed"]
        self.health = cfg["health"]
        self.invincible = cfg["invincible"]

        # -------------------------------------------------------
        # Collision setup
        # -------------------------------------------------------
        self.collision_tag = "player"
        self.hitbox_scale = cfg["hitbox_scale"]
        self.hitbox = CollisionHitbox(self, self.hitbox_scale)
        self.has_hitbox = True

        # -------------------------------------------------------
        # Combat / Shooting
        # -------------------------------------------------------
        self.bullet_manager = None       # Linked externally by GameScene
        self.shoot_cooldown = 0.1        # Seconds between shots
        self.shoot_timer = 0.0

        # -------------------------------------------------------
        # Layer & Global State
        # -------------------------------------------------------
        self.layer = Layers.PLAYER
        STATE.player_ref = self

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
        # max_speed = self.speed
        smooth_factor = 0.2   # Direction blending strength

        # -------------------------------------------------------
        # Movement & acceleration
        # -------------------------------------------------------
        if move_vec.length_squared() > 0:
            move_vec = move_vec.normalize()
            desired_velocity = move_vec * self.speed

            # Blend velocity toward desired direction
            self.velocity = self.velocity.lerp(desired_velocity, smooth_factor)
            self.velocity += move_vec * accel_rate * dt

            # Enforce max speed limit (prevents overshoot)
            if self.velocity.length() > self.speed:
                self.velocity.scale_to_length(self.speed)

        else:
            # Apply friction when idle
            current_speed = self.velocity.length()
            if current_speed > 0:
                new_speed = max(0.0, current_speed - friction_rate * dt)
                if new_speed < 5.0:
                    self.velocity.xy = (0, 0)
                else:
                    self.velocity.scale_to_length(new_speed)

        # -------------------------------------------------------
        # Position Update
        # -------------------------------------------------------
        self.pos += self.velocity * dt
        self._clamp_to_screen()

        # Update render rect
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

        # -------------------------------------------------------
        # Shooting Control
        # -------------------------------------------------------
        self.shoot_timer += dt
        keys = pygame.key.get_pressed()

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

        Args:
            other (BaseEntity): The other entity involved in the collision.
        """
        tag = getattr(other, "collision_tag", "unknown")

        if tag == "enemy":
            if not self.invincible:
                self.take_damage(1, source=type(other).__name__)
                other.alive = False
                DebugLogger.state("[Collision] Player collided with Enemy")

        elif tag == "enemy_bullet":
            if not self.invincible:
                self.take_damage(1, source="enemy_bullet")
                DebugLogger.state("[Collision] Player hit by Enemy Bullet")

        else:
            DebugLogger.trace(f"[Collision] Player ignored {tag}")

    # ===========================================================
    # Damage Handling
    # ===========================================================
    def take_damage(self, amount: int, source: str = "unknown"):
        """
        Reduce player health when damaged.
        Handles death, logging, and invincibility checks.

        Args:
            amount (int): Damage value.
            source (str): Cause or entity type.
        """
        if self.invincible:
            DebugLogger.trace(f"[DamageIgnored] Player invincible vs {source}")
            return

        self.health -= amount
        DebugLogger.state(f"[Damage] Player took {amount} from {source} → HP={self.health}")

        if self.health <= 0:
            self.alive = False
            DebugLogger.state("[Death] Player destroyed!")

    # ===========================================================
    # Utility: Screen Clamp
    # ===========================================================
    def _clamp_to_screen(self):
        """Ensure the player stays within screen bounds."""
        screen_w, screen_h = Display.WIDTH, Display.HEIGHT
        self.pos.x = max(0.0, min(self.pos.x, screen_w - self.rect.width))
        self.pos.y = max(0.0, min(self.pos.y, screen_h - self.rect.height))

        # Stop movement at edges
        if self.pos.x in (0, screen_w - self.rect.width):
            self.velocity.x = 0
        if self.pos.y in (0, screen_h - self.rect.height):
            self.velocity.y = 0
