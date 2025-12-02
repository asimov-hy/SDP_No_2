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
        'player_ref', 'base_angle', 'rotation_speed', 'min_angle', 'max_angle'
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

    def rotate_towards_player(self, player_ref):
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
        max_step = self.rotation_speed * (1 / 60)  # assuming update runs at 60 FPS
        step = max(-max_step, min(max_step, diff))
        self.angle += step

        # 4. Apply rotation
        final_angle = self.base_angle + self.angle
        self.image = pygame.transform.rotate(self._base_image, -final_angle)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

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

    __slots__ = ('parts', 'body_image', '_boss_config', 'player_ref')

    __registry_category__ = EntityCategory.ENEMY
    __registry_name__ = "boss"

    _boss_data = None  # Class-level cache for bosses.json

    @classmethod
    def _load_boss_data(cls):
        """Load and cache bosses.json."""
        if cls._boss_data is None:
            cls._boss_data = load_config("bosses.json") or {}
        return cls._boss_data

    def __init__(self, x, y, boss_type="mech_boss", draw_manager=None,
                 player_ref=None, bullet_manager=None, **kwargs):
        """
        Initialize boss from JSON config.

        Args:
            x, y: Spawn position
            boss_type: Key in bosses.json (e.g., "mech_boss")
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
            part_hp = part_cfg.get("hp", 20)

            # Create part
            self.parts[part_name] = BossPart(part_name, img, offset, part_hp, owner=self)

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
        for part in self.parts.values():
            if part.active:
                part.update_position(self.pos)
                # Rotate guns to track player
                if hasattr(self, 'player_ref') and self.player_ref:
                    part.rotate_towards_player(self.player_ref)

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

        draw_manager.draw_entity(self, layer=self.layer)

        for part in self.parts.values():
            if part.active and part.image:
                part_pos = (
                    self.rect.centerx + int(part.offset.x) - part.image.get_width() // 2,
                    self.rect.centery + int(part.offset.y) - part.image.get_height() // 2
                )
                part_rect = part.image.get_rect(topleft=part_pos)
                draw_manager.queue_draw(part.image, part_rect, layer=self.layer + 1)

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

    def reset(self, x, y, boss_type="mech_boss", **kwargs):
        config = self._boss_data.get(boss_type, {})
        body_cfg = config.get("body", {})
        super().reset(x, y, health=body_cfg.get("hp", 500), speed=config.get("speed", 50), **kwargs)