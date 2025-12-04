"""
boss_part.py
------------
Individual weapon/component attached to a boss entity.
Handles health, rotation, shooting, and collision independently.
"""

import pygame
import math

from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory, CollisionTags
from src.entities.entity_state import LifecycleState
from src.graphics.animations.animation_effects.damage_animation import damage_flash

class BossPart(BaseEntity):
    """..."""

    __slots__ = (
        # Part identity
        'name', 'owner', 'is_static', 'z_order',
        # Part transform (separate from entity rotation)
        'offset', 'angle',
        # Health
        'health', 'max_health', 'active',
        # Gun rotation
        'base_angle', 'rotation_speed', 'spray_speed', 'min_angle', 'max_angle',
        # Shooting
        'fire_rate', 'fire_timer', 'bullet_speed',
        'spray_bullet_image', 'trace_bullet_image',
        'spray_direction',
    )

    def __init__(self, name: str, image: pygame.Surface, offset: tuple,
                 health: int = 10, owner=None):
        """..."""
        # Initialize BaseEntity at origin (position updated by owner)
        super().__init__(x=0, y=0, image=image)

        # Part identity
        self.name = name
        self.owner = owner
        self.is_static = False
        self.z_order = 1

        # Part transform
        self.offset = pygame.Vector2(offset)
        self.angle = 0

        # Health
        self.health = health
        self.max_health = health
        self.active = True

        # Entity overrides
        self.category = EntityCategory.ENEMY
        self.collision_tag = CollisionTags.ENEMY

        # Gun rotation
        self.base_angle = 180
        self.rotation_speed = 120
        self.spray_speed = 45
        self.min_angle = -30
        self.max_angle = 30

        # Shooting
        self.fire_rate = 0.15
        self.fire_timer = 0.0
        self.bullet_speed = 400
        self.spray_bullet_image = None
        self.trace_bullet_image = None
        self.spray_direction = 1

    def is_offscreen(self) -> bool:
        """Parts never go offscreen independently."""
        return False

    def update_position(self, boss_pos, body_rotation=0):
        """
        Sync part position to boss body.
        Called each frame from boss._update_behavior().
        """
        rad = math.radians(body_rotation)
        cos_a, sin_a = math.cos(rad), math.sin(rad)

        rotated_offset_x = self.offset.x * cos_a - self.offset.y * sin_a
        rotated_offset_y = self.offset.x * sin_a + self.offset.y * cos_a

        self.pos.x = boss_pos.x + rotated_offset_x
        self.pos.y = boss_pos.y + rotated_offset_y

        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def rotate_towards_player(self, player_ref, dt=1/60):
        """Rotate gun to point at player with custom pivot."""
        if not self.active or not player_ref or not self._base_image:
            return

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

    def get_draw_image(self):
        """Return image with any active effects (flash) applied."""
        if self._anim_manager and self._anim_manager.active_type == "damage":
            t = self._anim_manager.timer / max(self._anim_manager.duration, 1e-6)
            intensity = int(255 * (1.0 - min(1.0, t)))
            img = self.image.copy()
            img.fill((intensity, intensity, intensity), special_flags=pygame.BLEND_RGB_ADD)
            return img
        return self.image

    def spray_rotate(self, dt=1 / 60):
        """Sweep gun back and forth within min/max angle range."""
        if not self.active or not self._base_image:
            return

        # Move angle in current direction
        step = self.spray_speed * dt * self.spray_direction
        self.angle += step

        # Reverse at limits
        if self.angle >= self.max_angle:
            self.angle = self.max_angle
            self.spray_direction = -1
        elif self.angle <= self.min_angle:
            self.angle = self.min_angle
            self.spray_direction = 1

        # Apply rotation
        final_angle = self.base_angle + self.angle
        self.image = pygame.transform.rotate(self._base_image, -final_angle)
        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # Re-apply damage flash after rotation (animation overwrites get lost)
        if self._anim_manager and self._anim_manager.active_type == "damage":
            t = self._anim_manager.timer / max(self._anim_manager.duration, 1e-6)
            damage_flash(self, min(1.0, t))

    def update_shooting(self, dt, bullet_manager, spray_mode=False):
        """Fire bullets in the direction the gun is pointing."""

        if not self.active or not bullet_manager:
            return

        self.fire_timer += dt
        if self.fire_timer < self.fire_rate:
            return

        self.fire_timer = 0.0

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

        # Select bullet based on mode
        bullet_img = self.spray_bullet_image if spray_mode else self.trace_bullet_image

        bullet_manager.spawn(
            pos=(spawn_x, spawn_y),
            vel=(vel_x, vel_y),
            image=bullet_img,
            owner="enemy",
            damage=1
        )
        # print(f"[BULLET SPAWNED] pos=({spawn_x:.0f}, {spawn_y:.0f}) vel=({vel_x:.0f}, {vel_y:.0f})")

    def on_collision(self, other, collision_tag=None):
        """
        Handle collision with other entities.
        Only responds to player bullets.
        """
        if not self.active or self.is_static:
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

        # Flash this part using existing animation system
        self.anim_manager.play("damage", duration=0.15)

        # Damage boss when part is hit (2x multiplier)
        if self.owner:
            self.owner.take_damage(amount * 2, source="part_damage")

        if self.health <= 0:
            self._destroy()

    def _destroy(self):
        """Handle part destruction."""
        self.active = False
        self.mark_dead(immediate=True)

        if self.hitbox:
            self.hitbox.set_active(False)

        if self.owner:
            self.owner._on_part_destroyed(self.name)

    def reset(self, x: float = 0, y: float = 0, **kwargs):
        """Reset part for boss pooling."""
        super().reset(x, y, **kwargs)
        self.health = self.max_health
        self.active = True
        self.angle = 0
        self.fire_timer = 0.0

        if self.hitbox:
            self.hitbox.set_active(True)