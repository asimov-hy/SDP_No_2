"""
player_base.py
--------------
Defines the Player entity and coordinates its movement, combat, and visual state.

Responsibilities
----------------
- Initialize the player sprite, hitbox, and configuration.
- Delegate per-frame logic to modular subsystems:
    - Movement → player_movement.py
    - Combat   → player_combat.py
- Maintain player-specific attributes such as health, invulnerability, and visibility.
"""

import pygame
import os
from src.core.game_settings import Display, Layers
from src.core.game_state import STATE
from src.core.utils.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.systems.combat.collision_hitbox import CollisionHitbox
from .player_config import PLAYER_CONFIG


class Player(BaseEntity):
    """Represents the controllable player entity."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x: float | None = None, y: float | None = None, image: pygame.Surface | None = None):
        """
        Initialize the player entity, load configuration, and prepare rendering and collision systems.

        Args:
            x (float | None): Optional x-coordinate for player spawn position.
            y (float | None): Optional y-coordinate for player spawn position.
            image (pygame.Surface | None): Optional preloaded player image surface.
        """
        cfg = PLAYER_CONFIG
        core = cfg["core_attributes"]
        default_state = cfg["default_shape"]

        # -------------------------------------------------------
        # 1) Visual setup (image or shape)
        # -------------------------------------------------------
        self.render_mode = cfg["render_mode"]
        if self.render_mode == "image":
            image = self._load_sprite(cfg, image)
            image = self._apply_scaling(core, image)

        # Compute spawn position
        x, y = self._compute_spawn_position(x, y, image)

        # -------------------------------------------------------
        # 2) BaseEntity initialization
        # -------------------------------------------------------
        super().__init__(
            x, y,
            image=image,
            render_mode=self.render_mode,
            shape_type=default_state["shape_type"],
            color=default_state["color"],
            size=default_state["size"],
        )

        # -------------------------------------------------------
        # 3) Core attributes
        # -------------------------------------------------------
        self.velocity = pygame.Vector2(0, 0)
        self.speed = core["speed"]
        self.health = core["health"]
        self.max_health = self.health
        self.invincible = core["invincible"]
        self.layer = Layers.PLAYER
        self.alive = True
        STATE.player_ref = self

        # -------------------------------------------------------
        # 4) Blinking / invulnerability
        # -------------------------------------------------------
        self.blinking = False
        self.blink_timer = 0.0
        self.blink_duration = 1.5      # Total invulnerability time (s)
        self.blink_interval = 0.1      # Flicker frequency (s)
        self.visible = True

        # -------------------------------------------------------
        # 5) Health-based visuals
        # -------------------------------------------------------
        self.image_states = cfg["image_states"]
        self.color_states = cfg["color_states"]
        self.health_thresholds = cfg["health_thresholds"]
        self.update_visual_state()

        # -------------------------------------------------------
        # 6) Collision setup
        # -------------------------------------------------------
        self.collision_tag = "player"
        self.hitbox_scale = core["hitbox_scale"]
        self.hitbox = CollisionHitbox(self, self.hitbox_scale)
        self.has_hitbox = True

        # -------------------------------------------------------
        # 7) Combat setup
        # -------------------------------------------------------
        self.bullet_manager = None
        self.shoot_cooldown = 0.1
        self.shoot_timer = 0.0

        DebugLogger.init(
            f"Initialized Player at ({x:.1f}, {y:.1f}) | Speed={self.speed} | HP={self.health}"
        )

    # ===========================================================
    # Helper Methods
    # ===========================================================
    @staticmethod
    def _load_sprite(cfg, image):
        """Load player sprite from disk or create a fallback if missing."""
        if image:
            return image
        path = cfg.get("sprite_path")
        if not path or not os.path.exists(path):
            DebugLogger.warn(f"[Player] Missing sprite: {path}, using fallback.")
            placeholder = pygame.Surface((64, 64))
            placeholder.fill((255, 50, 50))
            return placeholder
        image = pygame.image.load(path).convert_alpha()
        DebugLogger.state(f"Loaded sprite from {path}")
        return image

    @staticmethod
    def _apply_scaling(cfg, image):
        """Scale sprite according to configuration."""
        if not image or cfg["scale"] == 1.0:
            return image
        w, h = image.get_size()
        new_size = (int(w * cfg["scale"]), int(h * cfg["scale"]))
        image = pygame.transform.scale(image, new_size)
        DebugLogger.state(f"Sprite scaled to {new_size}")
        return image

    @staticmethod
    def _compute_spawn_position(x, y, image):
        """Compute initial spawn position relative to screen and sprite size."""
        img_w, img_h = image.get_size() if image else (64, 64)
        if x is None:
            x = (Display.WIDTH / 2) - (img_w / 2)
        if y is None:
            y = Display.HEIGHT - img_h - 10
        DebugLogger.state(f"Spawn position set to ({x:.1f}, {y:.1f})")
        return x, y

    # ===========================================================
    # Frame Cycle
    # ===========================================================
    def update(self, dt):
        """
        Update player state each frame by delegating to subsystems.

        Args:
            dt (float): Delta time since last frame in seconds.
        """
        if not self.alive:
            return

        from .player_movement import update_movement
        from .player_combat import update_shooting, update_blinking

        # Movement and combat updates
        move_vec = getattr(self, "move_vec", pygame.Vector2(0, 0))
        update_movement(self, dt, move_vec)
        update_shooting(self, dt)
        update_blinking(self, dt)

        # Collision update
        if self.hitbox:
            self.hitbox.update()

    def draw(self, draw_manager):
        """
        Render the player entity depending on mode and visibility.

        Args:
            draw_manager (DrawManager): The central draw manager used for queued rendering.
        """
        if not self.visible:
            return
        super().draw(draw_manager)

    def on_collision(self, other):
        """
        Delegate collision handling to the combat subsystem.

        Args:
            other (BaseEntity): The entity collided with.
        """
        from .player_combat import on_collision
        on_collision(self, other)

    # ===========================================================
    # Visual Update Logic
    # ===========================================================
    def update_visual_state(self):
        """
        Update the player’s sprite or color based on current health.

        Changes are determined by the thresholds defined in `player_config.py`.
        """
        hp = self.health
        th = self.health_thresholds
        mode = self.render_mode
        state = "normal"  # Default threshold name
        visual_value = None

        # -------------------------------------------------------
        # IMAGE MODE
        # -------------------------------------------------------
        if mode == "image":
            if hp <= th["critical"]:
                state = "damaged_critical"
            elif hp <= th["moderate"]:
                state = "damaged_moderate"

            path = self.image_states[state]
            visual_value = path

            try:
                self.image = pygame.image.load(path).convert_alpha()
            except Exception as e:
                DebugLogger.warn(f"[VisualState] Failed to load sprite: {path} ({e})")

        # -------------------------------------------------------
        # SHAPE MODE
        # -------------------------------------------------------
        elif mode == "shape":
            if hp <= th["critical"]:
                state = "damaged_critical"
            elif hp <= th["moderate"]:
                state = "damaged_moderate"

            self.color = self.color_states[state]
            visual_value = self.color

        # -------------------------------------------------------
        # Unified Debug Output
        # -------------------------------------------------------
        DebugLogger.state(
            f"Mode={mode} | HP={hp} | Threshold = {state} | Visual={visual_value}",
            category="effects"
        )

    def take_damage(self, amount: int):
        """
        Apply incoming damage to the player and refresh visuals.

        Args:
            amount (int): Amount of health to reduce.
        """
        self.health = max(0, self.health - amount)
        DebugLogger.state(f"Player took {amount} damage → HP={self.health}")
        self.update_visual_state()

        if self.health <= 0:
            self.alive = False
            DebugLogger.state("Player destroyed!")
