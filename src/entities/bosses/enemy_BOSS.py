"""
enemy_BOSS.py
--------------
Boss entity composed of a main body with multiple weapon attachments.
Loads configuration from bosses.json.
"""

import pygame

from src.entities.enemies.base_enemy import BaseEnemy
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory

from src.systems.entity_management.entity_registry import EntityRegistry

from src.core.services.config_manager import load_config
from src.core.debug.debug_logger import DebugLogger


class BossPart:
    """Individual weapon/component attached to the boss."""

    __slots__ = ('name', 'image', 'offset', 'health', 'max_health', 'active', 'angle')

    def __init__(self, name: str, image: pygame.Surface, offset: tuple, health: int = 10):
        self.name = name
        self.image = image
        self.offset = pygame.Vector2(offset)
        self.health = health
        self.max_health = health
        self.active = True
        self.angle = 0


class EnemyBoss(BaseEnemy):
    """Multi-part boss enemy with destructible components."""

    __slots__ = ('parts', 'body_image', 'phase', 'phase_thresholds',
                 'player_ref', 'bullet_manager', '_boss_config')

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
            boss_type: Key in bosses.json (e.g., "mech_boss")
        """
        boss_data = self._load_boss_data()
        config = boss_data.get(boss_type, {})
        self._boss_config = config

        # Body config
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

        # Load parts from config
        self.parts = {}
        self._load_parts(scale, config.get("parts", {}))

        # Phase system
        self.phase = 1
        self.phase_thresholds = config.get("phases", [0.75, 0.50, 0.25])

        # References
        self.player_ref = player_ref
        self.bullet_manager = bullet_manager

        DebugLogger.init(
            f"Spawned {boss_type} at ({x}, {y}) | HP={health} | Parts={len(self.parts)}",
            category="enemy"
        )

    def _load_parts(self, scale: float, parts_config: dict):
        """Load weapon parts from config."""
        for part_name, part_cfg in parts_config.items():
            image_path = part_cfg.get("image")
            img = BaseEntity.load_and_scale_image(image_path, scale)

            if img:
                if part_cfg.get("flip", False):
                    img = pygame.transform.flip(img, True, False)

                anchor = part_cfg.get("anchor", [0, 0])
                part_hp = part_cfg.get("hp", 20)

                self.parts[part_name] = BossPart(part_name, img, anchor, part_hp)

    def _update_behavior(self, dt: float):
        """Boss-specific behavior."""
        health_pct = self.health / self.max_health
        for i, threshold in enumerate(self.phase_thresholds):
            if health_pct <= threshold and self.phase <= i + 1:
                self.phase = i + 2
                self._on_phase_change(self.phase)
                break

    def _on_phase_change(self, new_phase: int):
        """Handle phase transition."""
        DebugLogger.state(f"Boss entered phase {new_phase}", category="enemy")

    def draw(self, surface: pygame.Surface):
        """Draw boss body and all active parts."""
        surface.blit(self.image, self.rect)

        for part in self.parts.values():
            if part.active and part.image:
                part_pos = (
                    self.rect.centerx + int(part.offset.x) - part.image.get_width() // 2,
                    self.rect.centery + int(part.offset.y) - part.image.get_height() // 2
                )
                surface.blit(part.image, part_pos)

    def damage_part(self, part_name: str, amount: int):
        """Damage a specific part."""
        if part_name in self.parts:
            part = self.parts[part_name]
            if part.active:
                part.health -= amount
                if part.health <= 0:
                    part.active = False
                    DebugLogger.state(f"Boss part '{part_name}' destroyed", category="enemy")

    def reset(self, x, y, boss_type="mech_boss", **kwargs):
        """Reset boss for pooling."""
        config = self._boss_data.get(boss_type, {})
        body_cfg = config.get("body", {})

        super().reset(x, y, health=body_cfg.get("hp", 500), speed=config.get("speed", 50), **kwargs)

        for part in self.parts.values():
            part.health = part.max_health
            part.active = True

        self.phase = 1