"""
shield.py
---------
Protective shield entity that follows an owner.
Blocks bullets, deflects enemies, reusable for player or items.
"""

import math
import pygame

from src.entities.base_entity import BaseEntity
from src.entities.entity_types import CollisionTags, EntityCategory
from src.entities.entity_state import InteractionState, LifecycleState
from src.core.runtime import Layers
from src.core.debug.debug_logger import DebugLogger
from src.graphics.particles.particle_manager import ParticleEmitter


class Shield(BaseEntity):
    """Protective shield that follows owner and handles collisions."""

    def __init__(self, owner, radius=56, color=(100, 200, 255), knockback_strength=350,
                 can_damage=False, damage_amount=0):
        """
        Args:
            owner: Entity to follow (Player, Item carrier, etc.)
            radius: Shield collision/visual radius
            color: Shield RGB color
            knockback_strength: Force applied to owner on enemy contact
            can_damage: If True, deals damage to enemies on contact
            damage_amount: Damage dealt to enemies (if can_damage)
        """
        self.owner = owner
        self.radius = radius
        self.color = color
        self.knockback_strength = knockback_strength
        self.can_damage = can_damage
        self.damage_amount = damage_amount

        # Create transparent surface for hitbox
        size = radius * 2
        image = pygame.Surface((size, size), pygame.SRCALPHA)

        super().__init__(owner.pos.x, owner.pos.y, image=image)

        # Shield config
        self.collision_tag = CollisionTags.SHIELD
        self.category = EntityCategory.ENVIRONMENT
        self.layer = Layers.PLAYER - 1  # Behind player
        self.state = InteractionState.DEFAULT

        # Visual state
        self._elapsed = 0.0
        self._visible = True

        # Hitbox config - circular, full radius
        self.hitbox_scale = 1.0
        self.hitbox_shape = "circle"

        DebugLogger.trace(f"Shield created for {type(owner).__name__}, radius={radius}")

    def update(self, dt):
        """Follow owner and update visuals."""
        if self.owner is None or self.owner.death_state != LifecycleState.ALIVE:
            self.kill()
            return

        # Follow owner position
        self.pos.x = self.owner.pos.x
        self.pos.y = self.owner.pos.y
        self.sync_rect()

        # Update visual animation
        self._elapsed += dt
        self._update_visual()

    def _update_visual(self):
        """Render shield with pulsing effect."""
        pulse = 0.5 + 0.5 * math.sin(self._elapsed * 4)
        alpha = int(80 + 40 * pulse)

        # Clear and redraw
        self.image.fill((0, 0, 0, 0))

        if self._visible:
            center = (self.radius, self.radius)

            # Outer glow
            glow_color = (*self.color, alpha // 3)
            pygame.draw.circle(self.image, glow_color, center, self.radius, 6)

            # Main ring
            ring_color = (*self.color, alpha)
            pygame.draw.circle(self.image, ring_color, center, self.radius - 4, 3)

            # Inner highlight
            highlight = tuple(min(255, c + 50) for c in self.color)
            pygame.draw.circle(self.image, (*highlight, alpha // 2), center, self.radius - 8, 2)

    def set_warning_blink(self, enabled, blink_rate=0.08):
        """Enable rapid blinking to warn shield ending."""
        if enabled:
            self._visible = int(self._elapsed / blink_rate) % 2 == 0
        else:
            self._visible = True

    def on_collision(self, other, collision_tag=None):
        """Handle shield collisions."""
        tag = collision_tag or getattr(other, "collision_tag", None)

        if tag == CollisionTags.ENEMY_BULLET:
            self._on_bullet_hit(other)

        elif tag == CollisionTags.ENEMY:
            self._on_enemy_hit(other)

    def _on_bullet_hit(self, bullet):
        """Destroy bullet and spawn particles."""
        # Destroy bullet
        if hasattr(bullet, 'kill'):
            bullet.kill()
        elif hasattr(bullet, 'active'):
            bullet.active = False

        # Visual feedback
        ParticleEmitter.burst("shield_impact", self.rect.center, count=5)
        DebugLogger.trace("Shield blocked bullet", category="collision")

    def _on_enemy_hit(self, enemy):
        """Push owner away from enemy, optionally damage enemy."""
        if self.owner is None:
            return

        # Calculate knockback direction (away from enemy)
        dx = self.owner.pos.x - enemy.pos.x
        dy = self.owner.pos.y - enemy.pos.y
        length = (dx * dx + dy * dy) ** 0.5

        if length > 0:
            direction = (dx / length, dy / length)
            self.owner.apply_knockback(direction, self.knockback_strength)

        # Deal damage if item shield
        if self.can_damage and self.damage_amount > 0:
            if hasattr(enemy, 'take_damage'):
                enemy.take_damage(self.damage_amount)
                DebugLogger.trace(f"Shield dealt {self.damage_amount} damage", category="collision")

        # Visual feedback
        ParticleEmitter.burst("shield_impact", self.rect.center, count=8,
                              direction=(dx, dy) if length > 0 else None)
        DebugLogger.trace("Shield deflected enemy", category="collision")

    def kill(self):
        """Clean up shield."""
        self.owner = None
        self.death_state = LifecycleState.DEAD
        DebugLogger.trace("Shield destroyed", category="collision")