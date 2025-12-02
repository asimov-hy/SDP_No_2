"""
enemy_boss.py
-------------
Boss entity composed of a main body with multiple weapon attachments.
Each part has independent health and can be destroyed.
Body becomes vulnerable to bullets only after all parts are destroyed.
"""

import pygame
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
        '_base_image', '_anim_manager', 'anim_context', 'category'
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

    __slots__ = ('parts', 'body_image', '_boss_config')

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