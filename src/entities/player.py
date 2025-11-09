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
import os

from src.core.game_settings import Display, Layers
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
    "speed": 300,   # Uses 300 from settings
    "health": 3,
    "invincible": False,
    "hitbox_scale": 0.85,
    "sprite_path": "assets/images/player.png",
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
    def __init__(self, x=None, y=None, image=None):
        """
        Initialize the player with position, attributes, and image scaling.

        Args:
            x (float | None): Optional x-coordinate.
            y (float | None): Optional y-coordinate.
            image (pygame.Surface | None): Optional preloaded image; loaded internally if None.
        """
        cfg = PLAYER_CONFIG

        # ---------------------------------------------------
        # 1) Load Sprite
        # ---------------------------------------------------
        image = self._load_sprite(cfg, image)

        # ---------------------------------------------------
        # 2) Apply Scaling
        # ---------------------------------------------------
        image = self._apply_scaling(cfg, image)

        # ---------------------------------------------------
        # 3) Determine Spawn Position
        # ---------------------------------------------------
        x, y = self._compute_spawn_position(x, y, image)

        # ---------------------------------------------------
        # 4) Initialize BaseEntity
        # ---------------------------------------------------
        super().__init__(x, y, image)

        # ---------------------------------------------------
        # 5) Core Attributes
        # ---------------------------------------------------
        self.velocity = pygame.Vector2(0, 0)
        self.speed = cfg["speed"]
        self.health = cfg["health"]
        self.invincible = cfg["invincible"]

        # ---------------------------------------------------
        # 6) Collision / Hitbox Setup
        # ---------------------------------------------------
        self.collision_tag = "player"
        self.hitbox_scale = cfg["hitbox_scale"]
        self.hitbox = CollisionHitbox(self, self.hitbox_scale)
        self.has_hitbox = True

        # ---------------------------------------------------
        # 7) Combat / Shooting
        # ---------------------------------------------------
        self.bullet_manager = None
        self.shoot_cooldown = 0.1
        self.shoot_timer = 0.0

        # ---------------------------------------------------
        # 8) Layer & Global State
        # ---------------------------------------------------
        self.layer = Layers.PLAYER
        STATE.player_ref = self

        DebugLogger.init(
            f"Initialized Player at ({x:.1f}, {y:.1f}) | Speed={self.speed} | HP={self.health}"
        )

    # =======================================================
    # Initialization Helpers
    # =======================================================
    @staticmethod
    def _load_sprite(cfg, image):
        """Load player sprite from disk or create fallback."""
        if image:
            return image

        sprite_path = cfg.get("sprite_path", "assets/images/player.png")

        if not os.path.exists(sprite_path):
            DebugLogger.warn(f"[Player] Missing sprite: {sprite_path}, using fallback.")
            placeholder = pygame.Surface((64, 64))
            placeholder.fill((255, 50, 50))
            return placeholder

        image = pygame.image.load(sprite_path).convert_alpha()
        DebugLogger.state(f"[Player] Loaded sprite from {sprite_path}")
        return image

    @staticmethod
    def _apply_scaling(cfg, image):
        """Apply scaling to player sprite if configured."""
        if not image or cfg["scale"] == 1.0:
            return image

        w, h = image.get_size()
        new_size = (int(w * cfg["scale"]), int(h * cfg["scale"]))
        image = pygame.transform.scale(image, new_size)
        DebugLogger.state(f"[Player] Sprite scaled to {new_size}")
        return image

    @staticmethod
    def _compute_spawn_position(x, y, image):
        """Compute default or given spawn position."""
        img_w, img_h = image.get_size() if image else (64, 64)
        if x is None:
            x = (Display.WIDTH / 2) - (img_w / 2)
        if y is None:
            y = Display.HEIGHT - img_h - 10
        DebugLogger.state(f"[Player] Spawn position set to ({x:.1f}, {y:.1f})")
        return x, y

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
        self._update_movement(dt, move_vec)
        self._update_shooting(dt)
        if self.hitbox:
            self.hitbox.update()

    # -------------------------------------------------------
    # Movement
    # -------------------------------------------------------
    def _update_movement(self, dt, move_vec):
        """Handle movement physics and velocity control."""
        accel_rate = 3000
        friction_rate = 500

        if move_vec.length_squared() > 0:
            move_vec = move_vec.normalize()
            desired_velocity = move_vec * self.speed
            self.velocity = self.velocity.lerp(desired_velocity, 0.25)
            self.velocity += move_vec * accel_rate * dt

            # Limit maximum speed
            max_speed = self.speed * 1.8
            if self.velocity.length() > max_speed:
                self.velocity.scale_to_length(max_speed)
        else:
            # Friction when idle
            current_speed = self.velocity.length()
            if current_speed > 0:
                new_speed = max(0.0, current_speed - friction_rate * dt)
                if new_speed < 5.0:
                    self.velocity.xy = (0, 0)
                else:
                    self.velocity.scale_to_length(new_speed)

        # Apply velocity to position
        self.pos += self.velocity * dt
        self._clamp_to_screen()
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

    # -------------------------------------------------------
    # Shooting
    # -------------------------------------------------------
    def _update_shooting(self, dt):
        """Manage shooting cooldown and bullet spawn."""
        self.shoot_timer += dt
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE] and self.shoot_timer >= self.shoot_cooldown:
            self.shoot_timer = 0.0
            self.shoot()

    def shoot(self):
        """Spawn bullets via BulletManager."""
        if not self.bullet_manager:
            DebugLogger.warn("[Player] Attempted to shoot without BulletManager")
            return

        self.bullet_manager.spawn(
            pos=self.rect.center,
            vel=(0, -900),
            color=(255, 255, 100),
            radius=4,
            owner="player",
        )

    # =======================================================
    # Collision & Damage
    # =======================================================
    def on_collision(self, other):
        """Handle collisions with enemies or projectiles."""
        tag = getattr(other, "collision_tag", "unknown")

        if tag == "enemy" and not self.invincible:
            self.take_damage(1, source=type(other).__name__)
        elif tag == "enemy_bullet" and not self.invincible:
            DebugLogger.state("[Collision] Player hit by Enemy Bullet")
            self.take_damage(1, source="enemy_bullet")
        else:
            DebugLogger.trace(f"[Collision] Player ignored {tag}")

    def take_damage(self, amount: int, source: str = "unknown"):
        """Reduce health when taking damage."""
        if self.invincible:
            DebugLogger.trace(f"Player invincible vs {source}")
            return

        self.health -= amount
        DebugLogger.state(f"Took {amount} from {source} → HP={self.health}")

        if self.health <= 0:
            self.alive = False
            DebugLogger.state("Player destroyed!")

    # =======================================================
    # Utility
    # =======================================================
    def _clamp_to_screen(self):
        """Ensure the player stays within screen bounds."""
        screen_w, screen_h = Display.WIDTH, Display.HEIGHT
        self.pos.x = max(0.0, min(self.pos.x, screen_w - self.rect.width))
        self.pos.y = max(0.0, min(self.pos.y, screen_h - self.rect.height))

        # Stop velocity at edges
        if self.pos.x in (0, screen_w - self.rect.width):
            self.velocity.x = 0
        if self.pos.y in (0, screen_h - self.rect.height):
            self.velocity.y = 0
