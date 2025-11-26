"""
base_entity.py
--------------
Foundational class for all active in-game entities (Player, Enemy, Bullet, Item).

Coordinate System
-----------------
All entities use center-based coordinates:
- self.pos represents the entity's visual and physical center
- self.rect.center is always synchronized with self.pos
- Movement, rotation, and collisions are relative to center

Rendering Modes
---------------
1. Image mode (fastest):
   Entity(x, y, image=sprite)

2. Shape mode (auto-optimized):
   Entity(x, y, shape_data={"type": "circle", "color": (255,0,0), "size": (8,8)}, draw_manager=dm)

3. Shape fallback (prototyping only - slow):
   Entity(x, y, shape_data={...})
"""

import os
import pygame
from typing import Optional

from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Layers, Bounds, Display
from src.entities.entity_state import LifecycleState
from src.entities.entity_types import EntityCategory, CollisionTags


class BaseEntity:
    """
    Base class for all game entities.

    Subclassed by Player, Enemy, Bullet, Item, Obstacle, Hazard, etc.
    """

    # ===================================================================
    # Class Constants
    # ===================================================================

    _CLEANUP_MARGINS = {
        EntityCategory.ENEMY: Bounds.ENEMY_CLEANUP_MARGIN,
        EntityCategory.PROJECTILE: Bounds.BULLET_ENEMY_MARGIN,
        EntityCategory.PICKUP: Bounds.ITEM_CLEANUP_MARGIN,
        EntityCategory.ENVIRONMENT: Bounds.ENV_CLEANUP_MARGIN,
    }

    _DAMAGE_MARGINS = {
        EntityCategory.ENEMY: Bounds.ENEMY_DAMAGE_MARGIN,
        EntityCategory.ENVIRONMENT: Bounds.ENV_DAMAGE_MARGIN,
    }

    # Rotation: 16 steps = 22.5° per step (good for pixel art)
    # Override in subclass for smoother rotation (e.g., 36 steps = 10°)
    ROTATION_STEPS = 16
    ROTATION_INCREMENT = 360 / ROTATION_STEPS

    # ===================================================================
    # Memory Layout
    # ===================================================================

    __slots__ = (
        # Core spatial
        'pos', 'rect', 'image', 'draw_manager',

        # State
        'death_state', 'layer', 'category', 'collision_tag', 'tags',

        # Rotation
        'rotation_angle', '_rotation_enabled', '_base_image',
        '_rotation_cache', '_cached_rotation_index',

        # Animation (lazy-loaded)
        '_anim_manager', 'anim_context',

        # Sprite states
        '_current_sprite', '_sprite_config', 'shape_data',

        # Hitbox
        'hitbox_scale', 'hitbox_shape', 'hitbox_offset', 'hitbox_params', 'hitbox',
    )

    # ===================================================================
    # Initialization
    # ===================================================================

    def __init__(
        self,
        x: float,
        y: float,
        image: Optional[pygame.Surface] = None,
        shape_data: Optional[dict] = None,
        draw_manager=None,
        hitbox_config: Optional[dict] = None
    ):
        """
        Initialize entity with position and rendering configuration.

        Args:
            x: Center X position
            y: Center Y position
            image: Pre-loaded sprite surface (mutually exclusive with shape_data)
            shape_data: Dict with 'type', 'color', 'size' for shape rendering
            draw_manager: DrawManager for shape prebaking (recommended)
            hitbox_config: Dict with 'scale', 'shape', 'offset' for collision
        """
        # Core position
        self.pos = pygame.Vector2(x, y)

        # Validate: can't use both image and shape_data
        if image is not None and shape_data is not None:
            raise ValueError(
                f"{type(self).__name__}: Cannot provide both 'image' AND 'shape_data'."
            )

        # Initialize shape_data (may be set below or remain None)
        self.shape_data = None

        # Acquire image surface
        self.image = self._acquire_image(image, shape_data, draw_manager)
        self._base_image = self.image
        self.draw_manager = draw_manager

        # Rect (center-aligned)
        self.rect = self.image.get_rect(center=(x, y))

        # Rotation system (lazy cache)
        self.rotation_angle = 0
        self._rotation_enabled = False
        self._rotation_cache = {}
        self._cached_rotation_index = -1

        # Entity state
        self.death_state = LifecycleState.ALIVE
        self.layer = Layers.ENEMIES
        self.category = EntityCategory.PARTICLE
        self.collision_tag = CollisionTags.NEUTRAL
        self.tags = set()

        # Sprite state system
        self._current_sprite = None
        self._sprite_config = {}

        # Animation (lazy-loaded via property)
        self._anim_manager = None
        self.anim_context = {}

        # Hitbox
        self._init_hitbox(hitbox_config)

    def _acquire_image(self, image, shape_data, draw_manager) -> pygame.Surface:
        """Resolve image from provided sources."""
        if image is not None:
            return image

        if draw_manager:
            size = shape_data["size"] if shape_data else (32, 32)
            color = shape_data["color"] if shape_data else None

            surface = draw_manager.get_entity_image(
                entity_type=type(self).__name__,
                size=size,
                color=color,
                config=shape_data
            )

            if shape_data:
                self.shape_data = shape_data
            return surface

        # Fallback: magenta placeholder
        if shape_data and not draw_manager:
            DebugLogger.warn(
                f"{type(self).__name__}: shape_data without draw_manager (slow rendering)"
            )

        size = shape_data.get("size", (32, 32)) if shape_data else (32, 32)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        surface.fill((255, 0, 255))
        return surface

    def _init_hitbox(self, config: Optional[dict]):
        """Initialize hitbox configuration."""
        config = config or {}
        self.hitbox_scale = config.get('scale', 0.9)
        self.hitbox_shape = config.get('shape', 'rect')
        self.hitbox_offset = config.get('offset', (0, 0))
        self.hitbox_params = {
            k: v for k, v in config.items()
            if k not in ('scale', 'shape', 'offset')
        }
        self.hitbox = None  # Populated by CollisionManager

    # ===================================================================
    # Properties
    # ===================================================================

    @property
    def anim_manager(self):
        """Lazy-load AnimationManager on first access."""
        if self._anim_manager is None:
            from src.graphics.animations.animation_manager import AnimationManager
            self._anim_manager = AnimationManager(self)
        return self._anim_manager

    # ===================================================================
    # Core Update Loop
    # ===================================================================

    def update(self, dt: float):
        """
        Per-frame update. Override in subclasses.

        Args:
            dt: Delta time in seconds
        """
        pass

    def sync_rect(self):
        """Synchronize rect.center with self.pos."""
        self.rect.centerx = int(self.pos.x)
        self.rect.centery = int(self.pos.y)

    # ===================================================================
    # Lifecycle
    # ===================================================================

    def mark_dead(self, immediate: bool = False):
        """
        Transition entity to dying/dead state.

        Args:
            immediate: Skip DYING state, go straight to DEAD
        """
        if self.death_state == LifecycleState.DEAD:
            return

        if immediate or self.death_state == LifecycleState.DYING:
            self.death_state = LifecycleState.DEAD
        else:
            self.death_state = LifecycleState.DYING

        DebugLogger.state(
            f"[{type(self).__name__}] -> {self.death_state.name}",
            category="entity"
        )

    def reset(self, x: float, y: float, **kwargs):
        """
        Reset entity for object pooling reuse.

        Args:
            x: New X position
            y: New Y position
            **kwargs: Subclass-specific reset parameters
        """
        self.pos.update(x, y)
        self.death_state = LifecycleState.ALIVE

        # Reset rotation
        self.rotation_angle = 0
        self._cached_rotation_index = -1
        if self._rotation_enabled:
            self._rotation_cache.clear()

        # Restore base image
        if self._base_image:
            self.image = self._base_image

        # Reset animation
        if self._anim_manager is not None:
            self._anim_manager.stop()
        self.anim_context = {}

        self.sync_rect()

    # ===================================================================
    # Rendering
    # ===================================================================

    def draw(self, draw_manager):
        """Queue entity for rendering via DrawManager."""
        if self.image is None:
            DebugLogger.fail(f"{type(self).__name__} has None image!")
            return
        draw_manager.draw_entity(self, self.layer)

    def refresh_sprite(self, new_image=None, new_color=None, shape_type=None, size=None):
        """
        Rebuild entity visuals at runtime.

        Args:
            new_image: New sprite surface
            new_color: New color (requires shape_data)
            shape_type: Shape type override
            size: Size override
        """
        if new_image:
            self.image = new_image

        elif new_color and self.shape_data:
            if not self.draw_manager:
                DebugLogger.warn(f"{type(self).__name__} can't rebake - no draw_manager")
                return

            shape_type = shape_type or self.shape_data.get("type", "rect")
            size = size or self.shape_data.get("size", (10, 10))

            self.image = self.draw_manager.prebake_shape(
                type=shape_type,
                size=size,
                color=new_color
            )

        # Update base image and rect
        if self.image:
            self._base_image = self.image
            self.rotation_angle = 0
            self.rect = self.image.get_rect(center=self.pos)

            # Clear rotation cache (source image changed)
            if self._rotation_enabled:
                self._rotation_cache.clear()
                self._cached_rotation_index = -1

    # ===================================================================
    # Rotation System
    # ===================================================================

    def update_rotation(self, velocity=None):
        """
        Snap to nearest rotation step based on velocity direction.
        Uses lazy caching to avoid spawn-time CPU spikes.

        Args:
            velocity: Vector2 direction (uses self.velocity if None)
        """
        if not self._rotation_enabled or not self._base_image:
            return

        vel = velocity if velocity is not None else getattr(self, 'velocity', None)
        if vel is None or vel.length_squared() < 0.01:
            return

        # Calculate angle (sprite faces UP: 0, -1)
        angle = -pygame.math.Vector2(0, -1).angle_to(vel) % 360

        # Snap to nearest step
        index = int(round(angle / self.ROTATION_INCREMENT)) % self.ROTATION_STEPS

        # Apply only if changed
        if index != self._cached_rotation_index:
            self.image = self._get_rotated_surface(index)
            self.rect = self.image.get_rect(center=self.rect.center)
            self._cached_rotation_index = index
            self.rotation_angle = index * self.ROTATION_INCREMENT

    def _get_rotated_surface(self, index: int) -> pygame.Surface:
        """Get rotated surface from cache or generate on demand."""
        if index in self._rotation_cache:
            return self._rotation_cache[index]

        if not self._base_image:
            return self.image

        angle = index * self.ROTATION_INCREMENT
        rotated = pygame.transform.rotate(self._base_image, angle)
        self._rotation_cache[index] = rotated
        return rotated

    # ===================================================================
    # Collision
    # ===================================================================

    def on_collision(self, other: "BaseEntity", collision_tag=None):
        """
        Handle collision with another entity. Override in subclasses.

        Args:
            other: Entity this collided with
            collision_tag: Pre-captured tag (prevents race conditions)
        """
        pass

    # ===================================================================
    # Bounds & Visibility
    # ===================================================================

    def get_cleanup_margin(self) -> int:
        """Get offscreen margin for entity cleanup."""
        return self._CLEANUP_MARGINS.get(self.category, 200)

    def get_damage_margin(self) -> int:
        """Get margin for damage zone."""
        return self._DAMAGE_MARGINS.get(self.category, 0)

    def is_offscreen(self, margin: int = None) -> bool:
        """Check if entity is beyond cleanup margin."""
        m = margin if margin is not None else self.get_cleanup_margin()
        return (
            self.rect.right < -m or
            self.rect.left > Display.WIDTH + m or
            self.rect.bottom < -m or
            self.rect.top > Display.HEIGHT + m
        )

    def is_hittable(self) -> bool:
        """Check if entity is within damage zone."""
        m = self.get_damage_margin()
        return (
            self.rect.right > m and
            self.rect.left < Display.WIDTH - m and
            self.rect.bottom > m and
            self.rect.top < Display.HEIGHT - m
        )

    # ===================================================================
    # Sprite State System
    # ===================================================================

    def setup_sprite(self, health, thresholds_dict, color_states, image_states=None, render_mode="shape"):
        """
        Configure sprite state transitions based on health thresholds.

        Args:
            health: Current health value
            thresholds_dict: {state_name: health_threshold}
            color_states: {state_name: (r, g, b)}
            image_states: {state_name: surface} (optional)
            render_mode: "shape" or "image"
        """
        # Sort by threshold descending
        sorted_states = sorted(thresholds_dict.items(), key=lambda x: x[1], reverse=True)

        # Determine initial state
        state_key = None
        for name, threshold in sorted_states:
            if health <= threshold:
                state_key = f"damaged_{name}"
                break

        if state_key is None:
            state_key = next(iter(color_states.keys()))

        self._current_sprite = state_key
        self._sprite_config = {
            "thresholds": thresholds_dict,
            "colors": color_states,
            "images": image_states or {},
            "render_mode": render_mode
        }

    def get_current_color(self):
        """Get color for current sprite state."""
        return self._sprite_config.get('colors', {}).get(self._current_sprite, (255, 255, 255))

    def get_target_color(self, state_key):
        """Get color for specified sprite state."""
        return self._sprite_config.get('colors', {}).get(state_key, (255, 255, 255))

    def get_current_image(self):
        """Get image for current sprite state."""
        return self._sprite_config.get('images', {}).get(self._current_sprite)

    def get_target_image(self, state_key):
        """Get image for specified sprite state."""
        return self._sprite_config.get('images', {}).get(state_key)

    # ===================================================================
    # Utilities
    # ===================================================================

    def distance_to(self, other: "BaseEntity") -> float:
        """Calculate distance to another entity."""
        return self.pos.distance_to(other.pos)

    def has_tag(self, tag) -> bool:
        """Check if entity has a specific tag."""
        return tag == self.category or tag in self.tags

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} "
            f"pos=({self.pos.x:.1f}, {self.pos.y:.1f}) "
            f"tag={self.collision_tag} "
            f"category={getattr(self, 'category', '?')}>"
        )

    # ===================================================================
    # Static Utilities
    # ===================================================================

    @staticmethod
    def load_and_scale_image(image_path, scale=1.0, fallback_color=(255, 0, 255)):
        """
        Load and scale an image from disk.

        Args:
            image_path: Path to image file
            scale: Float or (width_scale, height_scale) tuple
            fallback_color: Color if load fails (unused, returns None)

        Returns:
            pygame.Surface or None
        """
        if image_path is None:
            return None

        if not os.path.exists(image_path):
            DebugLogger.warn(f"Image not found: {image_path}")
            return None

        try:
            img = pygame.image.load(image_path).convert_alpha()

            if isinstance(scale, (int, float)):
                new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
            elif isinstance(scale, (list, tuple)) and len(scale) == 2:
                new_size = (int(img.get_width() * scale[0]), int(img.get_height() * scale[1]))
            else:
                return img

            return pygame.transform.scale(img, new_size)

        except pygame.error as e:
            DebugLogger.fail(f"Pygame error loading {image_path}: {e}")
            return None
        except Exception as e:
            DebugLogger.fail(f"Failed loading {image_path}: {e}")
            return None