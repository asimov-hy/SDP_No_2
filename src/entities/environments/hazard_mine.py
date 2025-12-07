"""
Mine hazard - deploys to position, arms, explodes.
"""

import pygame
import math
from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory, CollisionTags
from src.core.runtime.game_settings import Layers


# ===================
# MINE CONFIG
# ===================
MINE_CONFIG = {
    "damage": 15,
    "damage_radius": 160,
    "deploy_speed": 400,
    "fuse_time": 3.0,
    "fade_time": 3.0,
    "sprite_radius": 25,
}


class MineState:
    """Mine lifecycle states."""

    DEPLOYING = 1
    ARMED = 2
    EXPLODING = 3


class MineExplosion(BaseEntity):
    """
    Instant full-radius explosion that fades out.
    Damages on spawn frame only.
    """

    __registry_category__ = EntityCategory.HAZARD
    __registry_name__ = "mine_explosion"

    def __init__(
        self,
        x,
        y,
        damage_radius,
        damage,
        fade_time=None,
        draw_manager=None,
        collision_manager=None,
        hazard_manager=None,
        **kwargs,
    ):
        super().__init__(x, y, draw_manager=draw_manager, **kwargs)

        self.category = EntityCategory.HAZARD
        self.collision_tag = CollisionTags.HAZARD

        self.damage_radius = damage_radius
        self.damage = damage
        self.fade_time = (
            fade_time if fade_time is not None else MINE_CONFIG["fade_time"]
        )
        self.fade_timer = 0.0

        self.collision_manager = collision_manager
        self._damaged_entities = set()
        self._hitbox_active = True

        if self.collision_manager:
            self.collision_manager.register_hitbox(
                self, shape="circle", shape_params={"radius": self.damage_radius}
            )

        self.rect = pygame.Rect(0, 0, 1, 1)
        self.rect.center = (int(x), int(y))

    def update(self, dt):
        """Fade out over time."""
        self.fade_timer += dt

        # Remove hitbox after first frame
        if self._hitbox_active and self.fade_timer > dt:
            if self.collision_manager:
                self.collision_manager.unregister_hitbox(self)
            self._hitbox_active = False

        if self.fade_timer >= self.fade_time:
            self.mark_dead(immediate=True)

    def on_collision(self, other, collision_tag=None):
        """Track damaged entities to prevent double-hits."""
        if collision_tag != "player":
            return
        if id(other) in self._damaged_entities:
            return
        self._damaged_entities.add(id(other))

    def draw(self, draw_manager):
        """Draw solid red circle that fades out."""
        progress = self.fade_timer / self.fade_time
        alpha = max(0, int(200 * (1.0 - progress)))

        size = int(self.damage_radius * 2) + 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        pygame.draw.circle(
            surf, (255, 50, 50, alpha), (center, center), int(self.damage_radius)
        )

        rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        draw_manager.queue_draw(surf, rect, layer=Layers.PICKUPS + 5)


class MineHazard(BaseEntity):
    """
    Proximity mine - explodes on player/bullet contact.
    """

    __registry_category__ = EntityCategory.HAZARD
    __registry_name__ = "mine"

    def __init__(
        self,
        x,
        y,
        target_x=None,
        target_y=None,
        deploy_speed=None,
        damage=None,
        damage_radius=None,
        draw_manager=None,
        hazard_manager=None,
        collision_manager=None,
        **kwargs,
    ):
        super().__init__(x, y, draw_manager=draw_manager, **kwargs)

        self.category = EntityCategory.HAZARD
        self.collision_tag = CollisionTags.HAZARD

        self.target_x = target_x if target_x is not None else x
        self.target_y = target_y if target_y is not None else y

        self.deploy_speed = (
            deploy_speed if deploy_speed is not None else MINE_CONFIG["deploy_speed"]
        )
        self.damage = damage if damage is not None else MINE_CONFIG["damage"]
        self.damage_radius = (
            damage_radius if damage_radius is not None else MINE_CONFIG["damage_radius"]
        )
        self.hazard_manager = hazard_manager

        self.mine_state = MineState.DEPLOYING
        if self._at_target():
            self.mine_state = MineState.ARMED

        self.radius = MINE_CONFIG["sprite_radius"]
        self._base_image = self._load_image()
        self.image = self._base_image.copy()
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

        self.collision_manager = collision_manager
        if self.collision_manager:
            self.collision_manager.register_hitbox(
                self, shape="circle", shape_params={"radius": self.radius}
            )

    def _load_image(self):
        """Load mine sprite."""
        target_size = self.radius * 2
        img = BaseEntity.load_and_scale_image(
            "assets/images/sprites/projectiles/land_mine.png", scale=1.0
        )
        if img:
            scale_factor = target_size / max(img.get_width(), img.get_height())
            new_w = int(img.get_width() * scale_factor)
            new_h = int(img.get_height() * scale_factor)
            return pygame.transform.scale(img, (new_w, new_h))

        # Fallback
        size = self.radius * 2
        fallback = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(
            fallback, (255, 100, 0), (self.radius, self.radius), self.radius
        )
        return fallback

    def _at_target(self):
        """Check if mine reached target."""
        dx = self.target_x - self.pos.x
        dy = self.target_y - self.pos.y
        return (dx * dx + dy * dy) < 4

    def update(self, dt):
        """Update mine state."""
        if self.mine_state == MineState.DEPLOYING:
            self._update_deploying(dt)

        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def _update_deploying(self, dt):
        """Move toward target position."""
        dx = self.target_x - self.pos.x
        dy = self.target_y - self.pos.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 2:
            self.pos.x = self.target_x
            self.pos.y = self.target_y
            self.mine_state = MineState.ARMED
        else:
            move_dist = min(self.deploy_speed * dt, dist)
            self.pos.x += (dx / dist) * move_dist
            self.pos.y += (dy / dist) * move_dist

    def on_collision(self, other, collision_tag=None):
        """Trigger explosion on contact."""
        if self.mine_state != MineState.ARMED:
            return

        if collision_tag in ("player", "player_bullet"):
            self.explode()

    def explode(self):
        """Spawn explosion and destroy mine."""
        self.mine_state = MineState.EXPLODING

        if self.hazard_manager:
            self.hazard_manager.spawn(
                MineExplosion,
                self.pos.x,
                self.pos.y,
                damage_radius=self.damage_radius,
                damage=self.damage,
            )

        self.mark_dead(immediate=True)

    def draw(self, draw_manager):
        """Draw mine and warning circle."""
        if self.mine_state == MineState.EXPLODING:
            return

        if self.mine_state == MineState.ARMED:
            self._draw_damage_radius(draw_manager)

        draw_manager.queue_draw(self.image, self.rect, layer=Layers.PICKUPS + 10)

    def _draw_damage_radius(self, draw_manager):
        """Draw dotted orange circle."""
        size = int(self.damage_radius * 2) + 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        num_dots = 48
        for i in range(num_dots):
            angle = (2 * math.pi * i) / num_dots
            dot_x = center + int(self.damage_radius * math.cos(angle))
            dot_y = center + int(self.damage_radius * math.sin(angle))
            pygame.draw.circle(surf, (255, 100, 0, 150), (dot_x, dot_y), 4)

        rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        draw_manager.queue_draw(surf, rect, layer=Layers.PICKUPS + 1)


class TimedMine(MineHazard):
    """
    Mine that auto-explodes after fuse_time.
    Red circle shrinks to center, then explodes.
    """

    __registry_name__ = "timed_mine"

    def __init__(self, x, y, fuse_time=None, **kwargs):
        super().__init__(x, y, **kwargs)
        self.fuse_time = (
            fuse_time if fuse_time is not None else MINE_CONFIG["fuse_time"]
        )
        self.fuse_timer = 0.0

    def update(self, dt):
        """Update mine + fuse timer."""
        super().update(dt)

        if self.mine_state == MineState.ARMED:
            self.fuse_timer += dt
            if self.fuse_timer >= self.fuse_time:
                self.explode()

    def _draw_damage_radius(self, draw_manager):
        """Draw dotted orange + shrinking red circle."""
        size = int(self.damage_radius * 2) + 4
        center = size // 2

        # Fixed dotted orange circle
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        num_dots = 48
        for i in range(num_dots):
            angle = (2 * math.pi * i) / num_dots
            dot_x = center + int(self.damage_radius * math.cos(angle))
            dot_y = center + int(self.damage_radius * math.sin(angle))
            pygame.draw.circle(surf, (255, 100, 0, 150), (dot_x, dot_y), 4)

        rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        draw_manager.queue_draw(surf, rect, layer=Layers.PICKUPS + 1)

        # Shrinking red circle toward center
        progress = self.fuse_timer / self.fuse_time
        current_radius = self.damage_radius * (1.0 - progress)

        if current_radius > 2:
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            alpha = int(100 + 120 * progress)
            pygame.draw.circle(
                surf, (255, 50, 50, alpha), (center, center), int(current_radius), 3
            )

            rect = surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            draw_manager.queue_draw(surf, rect, layer=Layers.PICKUPS + 2)
