"""
enemy_boss.py
-------------
Boss entity composed of a main body with multiple weapon attachments.
Each part has independent health and can be destroyed.
Body becomes vulnerable to bullets only after all parts are destroyed.
"""

import pygame
import math
import random

from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory
from src.entities.entity_state import LifecycleState, InteractionState
from src.entities.entity_types import CollisionTags

from src.systems.entity_management.entity_registry import EntityRegistry
from src.graphics.animations.animation_manager import AnimationManager

from src.core.services.config_manager import load_config
from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Debug

class BossPart:
    """
    Individual weapon/component attached to the boss.

    Each part:
    - Has its own health pool
    - Can be independently targeted and destroyed
    - Syncs position to parent boss
    - Reports destruction to parent for vulnerability check
    """

    __slots__ = (
        'name', 'image', 'offset', 'health', 'max_health', 'active', 'angle',
        'owner', 'pos', 'rect', 'hitbox', 'collision_tag', 'death_state', 'state',
        '_base_image', '_anim_manager', 'anim_context', 'category',
        'player_ref', 'base_angle', 'rotation_speed', 'min_angle', 'max_angle',
        'fire_rate', 'fire_timer', 'bullet_speed', 'bullet_offset', 'bullet_image',
        'is_static', 'z_order'
    )

    def __init__(self, name: str, image: pygame.Surface, offset: tuple,
                 health: int = 10, owner=None):
        """
        Initialize a boss part.

        Args:
            name: Part identifier (e.g., "mg_left", "laser")
            image: Part sprite
            offset: Position offset from boss center
            health: Part HP
            owner: Parent EnemyBoss reference
        """
        self.name = name
        self.image = image
        self.offset = pygame.Vector2(offset)
        self.health = health
        self.max_health = health
        self.active = True
        self.angle = 0

        # Rotation pivot (offset from image center, towards top of gun)
        # Negative Y = pivot towards top of sprite
        # Pivot at exact center of the sprite

        self.player_ref = None
        self.base_angle = 180  # Default facing down (180°)

        # Rotation restrictions
        self.rotation_speed = 120  # degrees per second
        self.min_angle = -30  # left limit (relative to base_angle)
        self.max_angle = 30  # right limit (relative to base_angle)

        # Parent reference
        self.owner = owner

        # Position (updated each frame to follow boss)
        self.pos = pygame.Vector2(0, 0)
        self.rect = image.get_rect() if image else pygame.Rect(0, 0, 40, 40)

        # Collision system fields
        self.hitbox = None  # Assigned by CollisionManager.register_hitbox()
        self.collision_tag = "boss_part"
        self.death_state = LifecycleState.ALIVE
        self.state = InteractionState.DEFAULT
        self.category = EntityCategory.ENEMY

        # Animation support (sync with body)
        self._base_image = image
        self._anim_manager = None
        self.anim_context = {}

        # Shooting properties
        self.fire_rate = 0.15  # seconds between shots
        self.fire_timer = 0.0
        self.bullet_speed = 400
        self.bullet_offset = (0, 30)  # offset along gun direction
        self.bullet_image = None  # loaded by owner

    @property
    def anim_manager(self):
        """Lazy-load AnimationManager on first access."""
        if self._anim_manager is None:
            self._anim_manager = AnimationManager(self)
        return self._anim_manager

    def update_position(self, boss_pos):
        """
        Sync part position to boss body.
        Called each frame from boss._update_behavior().
        """
        self.pos.x = boss_pos.x + self.offset.x
        self.pos.y = boss_pos.y + self.offset.y
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def rotate_towards_player(self, player_ref, dt=1/60):
        """Rotate gun to point at player with custom pivot."""
        if not self.active or not player_ref or not self._base_image:
            return

        self.player_ref = player_ref

        # Calculate direction to player from gun position
        dx = player_ref.pos.x - self.pos.x
        dy = player_ref.pos.y - self.pos.y

        # Calculate angle (sprite faces DOWN by default, so base is 180)
        target_angle = math.degrees(math.atan2(dy, dx)) + 90  # +90 converts to "down-facing" reference

        # 1. Compute angle relative to base
        relative_angle = target_angle - self.base_angle

        # 2. Clamp within allowed range
        clamped = max(self.min_angle, min(self.max_angle, relative_angle))

        # 3. Smooth rotation towards target (rotation_speed degrees/sec)
        diff = clamped - self.angle
        max_step = self.rotation_speed * dt
        step = max(-max_step, min(max_step, diff))
        self.angle += step

        # 4. Apply rotation
        final_angle = self.base_angle + self.angle
        self.image = pygame.transform.rotate(self._base_image, -final_angle)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # NEW METHOD TO ADD:
    def update_shooting(self, dt, bullet_manager):
        """Fire bullets in the direction the gun is pointing."""
        print(f"[PART SHOOT] active={self.active}, bm={bullet_manager is not None}, timer={self.fire_timer:.2f}")
        if not self.active or not bullet_manager:
            return

        self.fire_timer += dt
        if self.fire_timer < self.fire_rate:
            return

        self.fire_timer = 0.0

        if not self.player_ref:
            return

        # Calculate firing direction from gun angle
        # base_angle + self.angle gives the world rotation
        fire_angle_deg = self.base_angle + self.angle
        fire_angle_rad = math.radians(fire_angle_deg)

        # Direction vector (down is 180°, so we need to convert)
        dir_x = math.sin(fire_angle_rad)
        dir_y = -math.cos(fire_angle_rad)

        # Spawn position: gun center + offset along firing direction
        muzzle_offset = self.image.get_height() / 2

        spawn_x = self.pos.x + dir_x * muzzle_offset
        spawn_y = self.pos.y + dir_y * muzzle_offset

        # Velocity
        vel_x = dir_x * self.bullet_speed
        vel_y = dir_y * self.bullet_speed

        bullet_manager.spawn(
            pos=(spawn_x, spawn_y),
            vel=(vel_x, vel_y),
            image=self.bullet_image,
            owner="enemy",
            damage=1
        )
        print(f"[BULLET SPAWNED] pos=({spawn_x:.0f}, {spawn_y:.0f}) vel=({vel_x:.0f}, {vel_y:.0f})")

    def on_collision(self, other, collision_tag=None):
        """
        Handle collision with other entities.
        Only responds to player bullets.
        """
        if not self.active:
            return

        tag = collision_tag or getattr(other, "collision_tag", "")

        if tag == "player_bullet":
            damage = getattr(other, "damage", 1)
            self.take_damage(damage)

    def take_damage(self, amount: int):
        """Apply damage to this part and boss (2x to boss)."""
        if not self.active:
            return

        self.health -= amount

        # Damage boss when part is hit (2x multiplier)
        if self.owner:
            self.owner.take_damage(amount * 2, source="part_damage")

        if self.health <= 0:
            self._destroy()

    def _destroy(self):
        """Handle part destruction."""
        self.active = False
        self.death_state = LifecycleState.DEAD

        # Disable hitbox
        if self.hitbox:
            self.hitbox.set_active(False)

        # Notify parent boss
        if self.owner:
            self.owner._on_part_destroyed(self.name)

    def reset(self):
        """Reset part for boss pooling."""
        self.health = self.max_health
        self.active = True
        self.death_state = LifecycleState.ALIVE
        self.state = InteractionState.DEFAULT

        if self.hitbox:
            self.hitbox.set_active(True)

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
        'parts', 'body_image', '_boss_config', 'player_ref',
        'anchor_pos', 'wander_radius', 'noise_time', 'noise_seed',
        'hover_velocity', 'bullet_manager', '_mg_bullet_image',
        'track_target_x', 'target_follow_rate', 'track_speed_max',
        'track_speed_multiplier', '_rotation_enabled', 'exp_value',
        'tilt_angle', 'tilt_max', 'tilt_speed', 'velocity_x'
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
        self.track_speed_max = 600
        self.track_speed_multiplier = 4.0

        self.tilt_angle = 0.0  # current tilt (degrees)
        self.tilt_max = 15.0  # max tilt angle
        self.tilt_speed = 5.0  # how fast to tilt (lerp rate)
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

        self._rotation_enabled = False
        self.exp_value = config.get("exp", 1000)

        self.anchor_pos = pygame.Vector2(x, y)

        # Noise-based hover settings
        self.wander_radius = 100
        self.noise_time = 0.0
        self.noise_seed = random.randint(0, 10000)
        self.hover_velocity = pygame.Vector2(0, 0)

        # Store bullet manager reference
        self.bullet_manager = bullet_manager
        print(f"[BOSS DEBUG] bullet_manager received: {bullet_manager is not None}")

        # Load MG bullet image
        self._mg_bullet_image = BaseEntity.load_and_scale_image(
            "assets/images/sprites/projectiles/tracer.png", 0.2
        )
        print(f"[BOSS DEBUG] _mg_bullet_image loaded: {self._mg_bullet_image is not None}")

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

            # Assign bullet image to MG parts
            if "mg" in part_name:
                part.bullet_image = self._mg_bullet_image
                print(f"[BOSS DEBUG] Part {part_name} bullet_image: {part.bullet_image is not None}")

            self.parts[part_name] = part

        # Sync positions
        for part in self.parts.values():
            part.update_position(self.pos)

    def _on_part_destroyed(self, part_name: str):
        """Called when a part is destroyed."""
        DebugLogger.state(f"Part '{part_name}' destroyed.", category="enemy")

    # ===================================================================
    # Update Logic
    # ===================================================================

    def _update_behavior(self, dt: float):
        """Boss-specific per-frame logic."""

        # 1. Calculate the drift
        self._update_wander(dt)
        self._update_tilt(dt)

        # 2. Sync Rect to new Position
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # 3. Update Parts (Standard)
        for part in self.parts.values():
            if part.active:
                part.update_position(self.pos)
                if getattr(part, 'is_static', False):
                    continue  # Static parts don't rotate or shoot
                if hasattr(self, 'player_ref') and self.player_ref:
                    part.rotate_towards_player(self.player_ref, dt)
                # Fire bullets from MG parts
                if "mg" in part.name:
                    part.update_shooting(dt, self.bullet_manager)

    def _update_wander(self, dt: float):
        self.noise_time += dt

        if self.player_ref:
            # 1. Ghost target follows player with delay
            target_dx = self.player_ref.pos.x - self.track_target_x
            self.track_target_x += target_dx * self.target_follow_rate * dt

            # 2. Boss chases ghost - speed scales with distance
            chase_dx = self.track_target_x - self.pos.x
            distance = max(0, abs(chase_dx) - 50)

            # Speed increases with distance, capped at max
            track_speed = min(distance * self.track_speed_multiplier, self.track_speed_max)

            # Move toward ghost
            if distance > 1:
                direction = 1 if chase_dx > 0 else -1
                max_move = track_speed * dt
                move_amount = min(distance, max_move) * direction
                self.pos.x += move_amount
                self.velocity_x = move_amount / dt  # track velocity for tilt
            else:
                self.velocity_x = 0.0

            # Y anchor unchanged
            self.anchor_pos.y = min(max(150, self.player_ref.pos.y - 200), 150)
            self.anchor_pos.x = self.pos.x

        # --- KEPT: Organic wobble ---
        vel_x = self._value_noise(self.noise_time * 1.5) * 20
        vel_y = self._value_noise(self.noise_time * 1.5 + 100) * 15

        target_vel = pygame.Vector2(vel_x, vel_y)
        self.hover_velocity += (target_vel - self.hover_velocity) * 0.1

        self.pos += self.hover_velocity * dt

        # --- KEPT: Spring back to anchor ---
        distance = self.pos.distance_to(self.anchor_pos)
        if distance > self.wander_radius:
            pull = (self.anchor_pos - self.pos).normalize() * (distance - self.wander_radius) * 2
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

        if abs(self.tilt_angle) > 0.5:
            rotated_img = pygame.transform.rotate(self.body_image, -self.tilt_angle)
            rotated_rect = rotated_img.get_rect(center=self.rect.center)
            draw_manager.queue_draw(rotated_img, rotated_rect, layer=self.layer)
        else:
            draw_manager.draw_entity(self, layer=self.layer)

        for part in self.parts.values():
            if part.active and part.image:
                # Rotate offset by body tilt
                rad = math.radians(self.tilt_angle)
                cos_a, sin_a = math.cos(rad), math.sin(rad)

                rotated_offset_x = part.offset.x * cos_a - part.offset.y * sin_a
                rotated_offset_y = part.offset.x * sin_a + part.offset.y * cos_a

                # Rotate part image to match body tilt
                if getattr(part, 'is_static', False):
                    # Static parts: rotate base image with body (match body's negative sign)
                    rotated_part_img = pygame.transform.rotate(part._base_image, -self.tilt_angle)
                else:
                    # Gun parts: already have tracking rotation applied, add tilt
                    rotated_part_img = pygame.transform.rotate(part.image, self.tilt_angle)

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

    # ===================================================================
    # Object Pooling
    # ===================================================================

    def reset(self, x, y, boss_type="boss_juggernaut", **kwargs):
        config = self._boss_data.get(boss_type, {})
        body_cfg = config.get("body", {})
        super().reset(x, y, health=body_cfg.get("hp", 500), speed=config.get("speed", 50), **kwargs)