"""
enemy_boss.py
-------------
Boss entity composed of a main body with multiple weapon attachments.
Each part has independent health and can be destroyed.
"""

import pygame
import math
import random

from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory
from src.entities.entity_state import LifecycleState, InteractionState
from src.entities.entity_types import CollisionTags
from src.entities.bosses.boss_attack_manager import BossAttackManager
from src.entities.bosses.boss_part import BossPart


from src.core.services.config_manager import load_config
from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Debug

class EnemyBoss(BaseEnemy):
    """
    Multi-part boss enemy with destructible components.

    Damage Flow:
    1. Player bullets hit parts -> parts take damage
    2. All parts destroyed -> body becomes vulnerable
    3. Player bullets hit body -> boss takes damage
    4. Body contact always damages player (regardless of vulnerability)

    Phases:
    - Boss transitions phases based on HP thresholds
    - Phase changes can trigger new attack patterns
    """

    __slots__ = (
        # Config
        '_boss_config', '_weapon_config',
        # References
        'player_ref', 'bullet_manager', 'attack_manager',
        # Parts
        'parts', 'body_image',
        # Bullet images (loaded from config)
        '_spray_bullet_img', '_trace_bullet_img',
        # Movement
        'anchor_pos', 'home_pos', 'entrance_complete',
        'wander_radius', 'noise_time', 'noise_seed', 'hover_velocity', 'bob_time',
        # Player tracking
        'track_target_x', 'target_follow_rate', 'track_speed_max', 'track_speed_multiplier',
        # Tilt
        'tilt_angle', 'tilt_max', 'tilt_speed', 'velocity_x', 'tilt_enabled',
        # Rotation
        'body_rotation',
        # Flags
        '_rotation_enabled', 'exp_value'
    )

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "boss"

    _boss_data = None  # Class-level cache for bosses.json

    @classmethod
    def _load_boss_data(cls):
        """Load and cache bosses.json."""
        if cls._boss_data is None:
            cls._boss_data = load_config("bosses.json") or {}
        return cls._boss_data

    def __init__(self, x, y, boss_type="boss_juggernaut", draw_manager=None,
                 player_ref=None, bullet_manager=None, **kwargs):
        """
        Initialize boss from JSON config.

        Args:
            x, y: Spawn position
            boss_type: Key in bosses.json (e.g., "boss_juggernaut")
            draw_manager: For rendering
            player_ref: Player entity reference (for targeting)
            bullet_manager: For spawning boss bullets
        """
        # Load config
        boss_data = self._load_boss_data()
        config = boss_data.get(boss_type, {})
        self._boss_config = config

        # Store player reference for gun tracking
        self.player_ref = player_ref

        # Body setup
        body_cfg = config.get("body", {})
        scale = body_cfg.get("scale", 0.5)
        health = body_cfg.get("hp", 500)
        speed = config.get("speed", 50)

        self.track_target_x = x
        self.target_follow_rate = 3.0
        self.track_speed_max = 300
        self.track_speed_multiplier = 2.0

        self.tilt_angle = 0.0  # current tilt (degrees)
        self.tilt_max = 15.0  # max tilt angle
        self.tilt_speed = 5.0  # how fast to tilt (lerp rate)
        self.tilt_enabled = False  # toggle body tilt
        self.body_rotation = 0.0  # Attack-controlled rotation

        self.velocity_x = 0.0  # track horizontal velocity

        # Load body image
        body_path = body_cfg.get("image", "assets/images/sprites/boss/boss.png")
        body_img = BaseEntity.load_and_scale_image(body_path, scale)

        if body_img is None:
            body_img = pygame.Surface((200, 150), pygame.SRCALPHA)
            body_img.fill((100, 100, 100))

        self.body_image = body_img

        hitbox_config = body_cfg.get("hitbox", {"scale": 0.8, "shape": "rect"})

        # Initialize base enemy
        super().__init__(
            x, y,
            image=body_img,
            draw_manager=draw_manager,
            speed=speed,
            health=health,
            direction=(0, 0),
            hitbox_config=hitbox_config
        )

        self.exp_value = config.get("exp", 1000)

        # Home position is where boss should end up (on-screen)
        home_y = config.get("home_y", 150)  # Default 150px from top
        self.home_pos = pygame.Vector2(x, home_y)
        self.anchor_pos = pygame.Vector2(x, home_y)
        self.entrance_complete = False

        # Noise-based hover settings
        self.wander_radius = 100
        self.noise_time = 0.0
        self.noise_seed = random.randint(0, 10000)
        self.hover_velocity = pygame.Vector2(0, 0)
        self.bob_time = 0.0

        # Store bullet manager reference
        self.bullet_manager = bullet_manager

        # Load weapon config from JSON
        self._weapon_config = config.get("weapon_config", {})
        self._load_weapon_images()

        # Attack manager
        self.attack_manager = BossAttackManager(self, bullet_manager)

        # Load weapon parts
        self.parts = {}
        self._create_gun_parts(scale)
        self.collision_tag = CollisionTags.ENEMY

        DebugLogger.init(
            f"Spawned {boss_type} at ({x}, {y}) | HP={health} | Parts={len(self.parts)}",
            category="enemy"
        )

    # ===================================================================
    # Part Management
    # ===================================================================

    def _load_weapon_images(self):
        """Load bullet images from weapon_config."""
        cfg = self._weapon_config
        spray_cfg = cfg.get("spray_bullet", {})
        trace_cfg = cfg.get("trace_bullet", {})

        self._spray_bullet_img = BaseEntity.load_and_scale_image(
            spray_cfg.get("image"), spray_cfg.get("scale", 1.0)
        ) if spray_cfg.get("image") else None

        self._trace_bullet_img = BaseEntity.load_and_scale_image(
            trace_cfg.get("image"), trace_cfg.get("scale", 1.0)
        ) if trace_cfg.get("image") else None

    def _create_gun_parts(self, scale: float):
        """Create gun attachments from JSON config."""
        parts_config = self._boss_config.get("parts", {})

        for part_name, part_cfg in parts_config.items():
            # Load image
            image_path = part_cfg.get("image")
            part_scale = part_cfg.get("scale", 1.0) * scale

            img = BaseEntity.load_and_scale_image(image_path, part_scale)
            if not img:
                continue

            # Apply flip if configured
            if part_cfg.get("flip", False):
                img = pygame.transform.flip(img, True, False)

            # Get offset (scaled with body)
            anchor = part_cfg.get("anchor", [0, 0])
            offset = (anchor[0] * scale, anchor[1] * scale)

            # Get HP
            is_static = part_cfg.get("static", False)
            part_hp = 0 if is_static else part_cfg.get("hp", 20)
            part = BossPart(part_name, img, offset, part_hp, owner=None if is_static else self)
            part.is_static = is_static
            part.z_order = part_cfg.get("z_order", 1)

            # Alternate spray direction for opposite sweep
            if "left" in part_name:
                part.spray_direction = 1
            elif "right" in part_name:
                part.spray_direction = -1

            # Apply shared weapon config to gun parts (not static)
            if not is_static:
                self._apply_weapon_config(part)

            # Per-part overrides (from parts config)
            part.min_angle = part_cfg.get("min_angle", part.min_angle)
            part.max_angle = part_cfg.get("max_angle", part.max_angle)
            part.base_angle = part_cfg.get("base_angle", part.base_angle)

            self.parts[part_name] = part

        # Sync positions
        for part in self.parts.values():
            part.update_position(self.pos)

    def _apply_weapon_config(self, part):
        """Apply shared weapon settings to a gun part."""
        cfg = self._weapon_config
        part.fire_rate = cfg.get("fire_rate", part.fire_rate)
        part.bullet_speed = cfg.get("bullet_speed", part.bullet_speed)
        part.spray_speed = cfg.get("spray_speed", part.spray_speed)
        part.rotation_speed = cfg.get("rotation_speed", part.rotation_speed)
        part.spray_bullet_image = self._spray_bullet_img
        part.trace_bullet_image = self._trace_bullet_img

    def _on_part_destroyed(self, part_name: str):
        """Called when a part is destroyed."""
        DebugLogger.state(f"Part '{part_name}' destroyed.", category="enemy")

    # ===================================================================
    # Update Logic
    # ===================================================================

    def _update_behavior(self, dt: float):
        """Boss-specific per-frame logic."""

        # 1. Movement (check for attack override)
        movement_override = self.attack_manager.get_movement_override()
        if movement_override:
            self.pos.x += movement_override[0] * dt
            self.pos.y += movement_override[1] * dt
        else:
            self._update_wander(dt)

        if self.tilt_enabled:
            self._update_tilt(dt)

        # 2. Sync Rect to new Position
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # 3. Update part positions
        for part in self.parts.values():
            if part.active:
                part.update_position(self.pos, self.body_rotation)
            if part._anim_manager:
                part._anim_manager.update(dt)

        # 4. Update attack manager (handles part rotation + shooting)
        self.attack_manager.update(dt)

    def _update_wander(self, dt: float):
        self.noise_time += dt

        # Skip wander if attack has full position control
        override = self.attack_manager.get_movement_override()
        if override == (0, 0):
            return

            # Entrance phase: move toward home position
        if not self.entrance_complete:
            direction = self.home_pos - self.pos
            dist = direction.length()
            if dist < 5:
                self.entrance_complete = True
                self.pos.xy = self.home_pos.xy
            else:
                direction.normalize_ip()
                self.pos += direction * 150 * dt  # entrance speed
            return  # Skip normal movement during entrance

        # Only track player when ATTACKING, hover near spawn when IDLE
        is_attacking = self.attack_manager.state == "ATTACKING"

        if self.player_ref and is_attacking:
            # 1. Ghost target follows player with delay
            target_dx = self.player_ref.pos.x - self.track_target_x
            self.track_target_x += target_dx * self.target_follow_rate * dt

            # 2. Boss chases ghost - speed scales with distance
            chase_dx = self.track_target_x - self.pos.x
            distance = max(0, abs(chase_dx) - 50)
            track_speed = min(distance * self.track_speed_multiplier, self.track_speed_max)

            if distance > 1:
                direction = 1 if chase_dx > 0 else -1
                max_move = track_speed * dt
                move_amount = min(distance, max_move) * direction
                self.pos.x += move_amount
                self.velocity_x = move_amount / dt
            else:
                self.velocity_x = 0.0

            # Clamp X position to screen bounds (with padding for boss width)
            half_width = self.rect.width // 2
            screen_width = 1280  # Or get from display_manager
            padding = 20
            self.pos.x = max(half_width + padding, min(screen_width - half_width - padding, self.pos.x))

            min_y = 100  # Don't go too high
            max_y = 300  # Don't go too low
            self.anchor_pos.y = min(max(min_y, self.player_ref.pos.y - 200), max_y)
            self.anchor_pos.x = self.pos.x
        else:
            # IDLE: smoothly return anchor to home
            return_speed = 1.0  # Adjust for faster/slower return
            self.anchor_pos.x += (self.home_pos.x - self.anchor_pos.x) * return_speed * dt
            self.anchor_pos.y += (self.home_pos.y - self.anchor_pos.y) * return_speed * dt
            self.velocity_x *= 0.95  # Gradual slowdown

        # --- Layered noise: slow drift + faster jitter ---
        drift_x = self._value_noise(self.noise_time * 0.8) * 40
        drift_y = self._value_noise(self.noise_time * 0.8 + 100) * 25
        jitter_x = self._value_noise(self.noise_time * 3.0 + 200) * 15
        jitter_y = self._value_noise(self.noise_time * 3.0 + 300) * 10

        vel_x = drift_x + jitter_x
        vel_y = drift_y + jitter_y

        # --- Vertical bobbing (sine wave) ---
        self.bob_time += dt
        bob_offset = math.sin(self.bob_time * 2.5) * 4  # 2.5 Hz, 8px amplitude

        target_vel = pygame.Vector2(vel_x, vel_y + bob_offset * 10)
        self.hover_velocity += (target_vel - self.hover_velocity) * 0.25  # Snappier response

        self.pos += self.hover_velocity * dt

        # --- Tighter spring back to anchor ---
        distance = self.pos.distance_to(self.anchor_pos)
        if distance > self.wander_radius:
            pull = (self.anchor_pos - self.pos).normalize() * (distance - self.wander_radius) * 4
            self.pos += pull * dt

    def _update_tilt(self, dt: float):
        """Tilt boss based on horizontal velocity."""
        speed_ratio = self.velocity_x / self.track_speed_max  # -1 to 1
        abs_ratio = abs(speed_ratio)

        # Smooth ramp: no tilt below 0.4, full tilt above 0.8
        threshold_min = 0.4
        threshold_max = 0.8

        if abs_ratio < threshold_min:
            tilt_strength = 0.0
        elif abs_ratio > threshold_max:
            tilt_strength = 1.0
        else:
            # Smooth interpolation between thresholds
            tilt_strength = (abs_ratio - threshold_min) / (threshold_max - threshold_min)

        target_tilt = -speed_ratio * self.tilt_max * tilt_strength

        self.tilt_angle += (target_tilt - self.tilt_angle) * self.tilt_speed * dt

    # ===================================================================
    # Noise Generation for Organic Movement
    # ===================================================================

    def _hash_noise(self, x: float) -> float:
        """Simple hash-based noise function."""
        x = (x + self.noise_seed) * 12.9898
        return (math.sin(x) * 43758.5453) % 1.0 * 2 - 1

    def _smooth_interpolate(self, a: float, b: float, t: float) -> float:
        """Smoothstep interpolation (ease in/out)."""
        t = t * t * (3 - 2 * t)
        return a + (b - a) * t

    def _value_noise(self, x: float) -> float:
        """Value noise - interpolate between hashed points."""
        floor_x = math.floor(x)
        frac_x = x - floor_x
        a = self._hash_noise(floor_x)
        b = self._hash_noise(floor_x + 1)
        return self._smooth_interpolate(a, b, frac_x)

    # ===================================================================
    # Collision Handling
    # ===================================================================
    def on_collision(self, other, collision_tag=None):
        """Use base enemy collision handling."""
        super().on_collision(other, collision_tag)

    # ===================================================================
    # Rendering
    # ===================================================================

    def draw(self, draw_manager):
        """Draw boss body and gun parts."""

        if self.death_state != LifecycleState.ALIVE:
            return

        total_rotation = self.tilt_angle + self.body_rotation
        if abs(total_rotation) > 0.5:
            rotated_img = pygame.transform.rotate(self.body_image, -total_rotation)
            rotated_rect = rotated_img.get_rect(center=self.rect.center)
            draw_manager.queue_draw(rotated_img, rotated_rect, layer=self.layer)
        else:
            draw_manager.draw_entity(self, layer=self.layer)

        self.attack_manager.draw(draw_manager)

        for part in self.parts.values():

            if part.active and part.image:
                # Rotate offset by body tilt + body rotation
                total_rotation = self.tilt_angle + self.body_rotation
                rad = math.radians(total_rotation)
                cos_a, sin_a = math.cos(rad), math.sin(rad)

                rotated_offset_x = part.offset.x * cos_a - part.offset.y * sin_a
                rotated_offset_y = part.offset.x * sin_a + part.offset.y * cos_a

                draw_img = part.get_draw_image()
                total_rotation = self.tilt_angle + self.body_rotation
                if getattr(part, 'is_static', False):
                    rotated_part_img = pygame.transform.rotate(draw_img, -total_rotation)
                else:
                    rotated_part_img = pygame.transform.rotate(draw_img, total_rotation)

                part_pos = (
                    self.rect.centerx + int(rotated_offset_x) - rotated_part_img.get_width() // 2,
                    self.rect.centery + int(rotated_offset_y) - rotated_part_img.get_height() // 2
                )
                part_rect = rotated_part_img.get_rect(topleft=part_pos)
                draw_manager.queue_draw(rotated_part_img, part_rect, layer=self.layer + part.z_order)

                # Debug: Draw pivot point
                if Debug.HITBOX_VISIBLE:
                    pivot_world = (int(part.pos.x), int(part.pos.y))

                    debug_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
                    pygame.draw.circle(debug_surf, (255, 0, 255), (5, 5), 5)  # Magenta pivot
                    pygame.draw.circle(debug_surf, (0, 255, 0), (5, 5), 2)  # Green center

                    draw_manager.queue_draw(debug_surf,
                                            debug_surf.get_rect(center=pivot_world), layer=self.layer + 2)

    # ===================================================================
    # Utility
    # ===================================================================

    def is_offscreen(self) -> bool:
        """Boss never dies from going off-screen."""
        return False

    def take_damage(self, amount: int, source: str = "unknown"):
        """Override to flash all parts when boss takes any damage."""
        super().take_damage(amount, source)

        # Flash all active parts whenever boss takes damage (body or part hit)
        if self.health > 0:
            for part in self.parts.values():
                if part.active:
                    part.anim_manager.play("damage", duration=0.15)
