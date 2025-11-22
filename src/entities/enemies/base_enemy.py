"""
base_enemy.py
--------------
Defines the shared base class for all enemy entities_animation.

Responsibilities
----------------
- Maintain core enemy properties (HP, speed, alive state).
- Handle common behaviors such as damage, destruction, and drawing.
- Provide a base interface for all enemy subclasses (straight, zigzag, shooter, etc.).
"""

import pygame
import random
from src.core.runtime.game_settings import Display, Layers
from src.core.debug.debug_logger import DebugLogger
from src.entities.base_entity import BaseEntity
from src.entities.entity_state import LifecycleState, InteractionState
from src.entities.entity_types import CollisionTags, EntityCategory
from src.systems.entity_management.entity_registry import EntityRegistry
from src.core.services.event_manager import get_events, EnemyDiedEvent, NukeUsedEvent


class BaseEnemy(BaseEntity):
    """Base class providing shared logic for all enemy entities_animation."""

    __slots__ = (
        'speed', 'health', 'max_health', 'exp_value',
        'velocity', '_last_rot_velocity', 'state', '_nuke_subscribed'
    )

    @staticmethod
    def _classify_zone(normalized_pos: float) -> str:
        """Classify position into corner/edge/center zones."""
        if normalized_pos < 0.25 or normalized_pos > 0.75:
            return "corner"
        elif normalized_pos < 0.40 or normalized_pos > 0.60:
            return "edge"
        else:
            return "center"

    # Direction lookup table (computed once at class load)
    _DIRECTION_MAP = {
        "top": {
            "corner_top": [(1, 1)],
            "edge_top": [(0, 1), (1, 1)],
            "center": [(0, 1), (-1, 1), (1, 1)],
            "edge_bottom": [(0, 1), (-1, 1)],
            "corner_bottom": [(-1, 1)]
        },
        "bottom": {
            "corner_top": [(1, -1)],
            "edge_top": [(0, -1), (1, -1)],
            "center": [(0, -1), (-1, -1), (1, -1)],
            "edge_bottom": [(0, -1), (-1, -1)],
            "corner_bottom": [(-1, -1)]
        },
        "left": {
            "corner_top": [(1, 1)],
            "edge_top": [(1, 0), (1, 1)],
            "center": [(1, 0), (1, -1), (1, 1)],
            "edge_bottom": [(1, 0), (1, -1)],
            "corner_bottom": [(1, -1)]
        },
        "right": {
            "corner_top": [(-1, 1)],
            "edge_top": [(-1, 0), (-1, 1)],
            "center": [(-1, 0), (-1, -1), (-1, 1)],
            "edge_bottom": [(-1, 0), (-1, -1)],
            "corner_bottom": [(-1, -1)]
        }
    }

    def __init_subclass__(cls, **kwargs):
        """Auto-register enemy subclasses when they're defined."""
        super().__init_subclass__(**kwargs)
        EntityRegistry.auto_register(cls)

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x, y, image=None, shape_data=None, draw_manager=None,
                 speed=100, health=None, direction=None, spawn_edge=None, **kwargs):
        """
        Args:
            x, y: Position
            image: Pre-made sprite (image mode)
            shape_data: Shape definition (shape mode)
            draw_manager: Required for shape mode
            speed: Movement speed
            health: HP
        """
        hitbox_config = kwargs.get('hitbox_config', {})

        super().__init__(x, y, image=image, shape_data=shape_data,
                         draw_manager=draw_manager, hitbox_config=hitbox_config)
        self.speed = speed
        self.health = health if health is not None else 1
        self.max_health = self.health

        self.exp_value = 0

        # Optimization: Store last rotation velocity to avoid redundant trig
        self._last_rot_velocity = pygame.Vector2(0, 0)

        self._rotation_enabled = True

        # Collision setup
        self.collision_tag = CollisionTags.ENEMY
        self.category = EntityCategory.ENEMY
        self.layer = Layers.ENEMIES

        # Initialize velocity
        self.velocity = pygame.Vector2(0, 0)
        self.state = InteractionState.DEFAULT

        if direction is None:
            dir_vec = self._auto_direction_from_edge(spawn_edge)
            self.velocity.xy = dir_vec.xy
        else:
            self.velocity.xy = direction

        # Normalize and apply speed
        if self.velocity.length_squared() > 0:
            self.velocity.normalize_ip()
            self.velocity *= self.speed

        self.update_rotation()

        self._nuke_subscribed = False
        self._subscribe_nuke()

    def _subscribe_nuke(self):
        if not self._nuke_subscribed:
            get_events().subscribe(NukeUsedEvent, self.on_nuke_used)
            self._nuke_subscribed = True

    # ===========================================================
    # Damage and State Handling
    # ===========================================================
    def on_damage(self, amount: int):
        """
        Optional visual or behavioral response when the enemy takes damage.
        Override in subclasses for hit flash, particles, etc.
        """
        pass

    def _on_anim_complete(self, entity, anim_name):
        """Callback for animation completion."""
        if anim_name == "damage":
            # Reset state to default so we can collide again
            self.state = InteractionState.DEFAULT

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """Default downward movement for enemies."""
        if self.death_state == LifecycleState.DYING:
            if self.anim_manager.update(dt):
                self.mark_dead(immediate=True)
            return

        if self.death_state != LifecycleState.ALIVE:
            return

        # Ensure animations (like damage blink) update while alive
        self.anim_manager.update(dt)

        self.pos.x += self.velocity.x * dt
        self.pos.y += self.velocity.y * dt
        self.sync_rect()

        # Optimization: Only calculate rotation if velocity changed significantly
        if self._rotation_enabled and self.velocity != self._last_rot_velocity:
            self.update_rotation()
            self._last_rot_velocity.xy = self.velocity.xy

        # Mark dead if off-screen
        if self.is_offscreen():
            self.mark_dead(immediate=True)

    def take_damage(self, amount: int, source: str = "unknown"):
        """
        Reduce health by the given amount and handle death.
        Calls on_damage() and on_death() hooks as needed.
        """
        if self.death_state != LifecycleState.ALIVE:
            return

        self.health = max(0, self.health - amount)

        if self.health > 0:
            # FIX: Set INTANGIBLE during damage animation so we don't hurt player
            # while invisible/blinking
            self.state = InteractionState.INTANGIBLE

            # Re-bind callback because stop() clears it
            self.anim_manager.on_complete = self._on_anim_complete

            # Play damage animation (0.15s blink)
            self.anim_manager.play("damage", duration=0.15)
            self.on_damage(amount)

        if self.health <= 0:
            self.mark_dead(immediate=False)
            self.on_death(source)

    def on_death(self, source):
        duration = getattr(self, "death_duration", 0.45)
        self.anim_manager.play("death", duration=duration, death_frames=self._death_frames)
        self.collision_tag = CollisionTags.NEUTRAL

        get_events().dispatch(EnemyDiedEvent(
            position=(self.rect.centerx, self.rect.centery),
            enemy_type_tag=self.__class__.__name__,
            exp=self.exp_value
        ))

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """Render the enemy sprite to the screen."""
        draw_manager.draw_entity(self, layer=self.layer)

    # ===========================================================
    # Collision Handling
    # ===========================================================
    def on_collision(self, other):
        """Default collision response for enemies."""
        tag = getattr(other, "collision_tag", "unknown")

        if tag == "player_bullet":
            self.take_damage(1, source="player_bullet")

        elif tag == "player":
            self.take_damage(1, source="player_contact")

        else:
            DebugLogger.trace(f"[CollisionIgnored] {type(self).__name__} vs {tag}")

    def _auto_direction_from_edge(self, edge):
        """Auto-calculate direction based on spawn edge and position."""

        # Validate/detect edge
        if edge is None:
            if self.pos.x < 0: edge = "left"
            elif self.pos.x > Display.WIDTH: edge = "right"
            elif self.pos.y < 0: edge = "top"
            elif self.pos.y > Display.HEIGHT: edge = "bottom"
            else: edge = "top"  # fallback

        edge = edge.lower()

        # Calculate normalized position on relevant axis
        width = Display.WIDTH
        height = Display.HEIGHT

        if edge in ["top", "bottom"]:
            norm_pos = self.pos.x / width
        else:  # left or right
            norm_pos = self.pos.y / height

        # Clamp to [0, 1]
        norm_pos = max(0.0, min(1.0, norm_pos))

        # Classify zone
        zone_type = self._classify_zone(norm_pos)

        # Determine lookup key
        if zone_type == "corner":
            sub_zone = "top" if norm_pos < 0.5 else "bottom"
            lookup_key = f"corner_{sub_zone}"
        elif zone_type == "edge":
            sub_zone = "top" if norm_pos < 0.5 else "bottom"
            lookup_key = f"edge_{sub_zone}"
        else:  # center
            lookup_key = "center"

        # Lookup directions
        options = self._DIRECTION_MAP.get(edge, {}).get(lookup_key, [(0, 1)])

        # Choose and return
        chosen = random.choice(options)

        return pygame.Vector2(chosen)

    def reset(self, x, y, direction=None, speed=None, health=None, spawn_edge=None, **kwargs):
        super().reset(x, y)

        # Reset state to DEFAULT in case it was pooled while blinking
        self.state = InteractionState.DEFAULT

        if speed is not None:
            self.speed = speed
        if health is not None:
            self.health = health
            self.max_health = health

        if direction is None:
            dir_vec = self._auto_direction_from_edge(spawn_edge)
            self.velocity.xy = dir_vec.xy
        else:
            self.velocity.xy = direction

        if self.velocity.length_squared() > 0:
            self.velocity.normalize_ip()
            self.velocity *= self.speed

        self.update_rotation()
        self._subscribe_nuke()

    def cleanup(self):
        """Explicitly unsubscribe to prevent zombie processing."""
        if hasattr(self, '_nuke_subscribed') and self._nuke_subscribed:
            get_events().unsubscribe(NukeUsedEvent, self.on_nuke_used)
            self._nuke_subscribed = False

    def on_nuke_used(self, event: NukeUsedEvent):
        """Kill enemy instantly when nuke is used."""
        self.take_damage(self.max_health + 1, source="nuke")

    def _reload_image_cached(self, image_path, scale):
        """Reload image only if not cached, or scale changed."""
        if hasattr(self, '_base_image') and self._base_image:
            # Reuse cached image
            self.image = self._base_image
            self.rect = self.image.get_rect(center=self.pos)
        else:
            # First load - cache it
            self.image = BaseEntity.load_and_scale_image(image_path, scale)
            self._base_image = self.image
            self.rect = self.image.get_rect(center=self.pos)