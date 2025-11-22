"""
base_entity.py
--------------
Defines the BaseEntity class, which serves as the foundational interface
for all active in-game entities (e.g., Player, Enemy, Bullet).

Coordinate System Standard
--------------------------
All entities in the 202X runtime use **center-based coordinates**:
- self.pos represents the entity's visual and physical center.
- self.rect.center is always synchronized with self.pos.
- Movement, rotation, and collisions are performed relative to this center.

Rendering
---------
Image mode (fastest):
    Entity(x, y, image=sprite)

Shape mode (auto-optimized):
    Entity(x, y, shape_data={"type": "circle", "color": (255,0,0), "size": (8,8)}, draw_manager=dm)
    Note: Always pass draw_manager to prebake shapes as images (~4x faster)

Shape fallback (prototyping only):
    Entity(x, y, shape_data={...})  # Slower, renders per-frame

Responsibilities
----------------
- Provide shared attributes such as image, rect, and alive state.
- Define consistent update and draw interfaces for all entities.
- Support both sprite-based and shape-based rendering with auto-optimization.
- Serve as the parent class for specialized gameplay entities.
"""

import os
import pygame
from typing import Optional
from src.core.runtime.game_settings import Layers, Bounds, Display
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState
from src.entities.entity_types import EntityCategory
from src.graphics.animations.animation_manager import AnimationManager


class BaseEntity:
    """
    Common interface for all entities within the game level.

    This class should be subclassed by all game entities (Player, Enemy, Bullet, etc.).
    """

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

    # Fixed memory slots for faster access and lower RAM usage
    __slots__ = (
        # Core spatial/visual
        'pos', 'image', 'rect', 'draw_manager',

        # Rotation system
        'rotation_angle', '_rotation_enabled', '_base_image',
        '_rotation_cache', '_cached_rotation_index',

        # State management
        'death_state', 'layer', 'category', 'collision_tag', 'tags',

        # Sprite/animation
        '_current_sprite', '_sprite_config', 'anim_manager',
        '_death_frames', '_damage_frames', 'anim_context',

        # Hitbox configuration
        'hitbox_scale', 'hitbox_shape', 'hitbox_offset', 'hitbox_params', 'hitbox',

        # Shape rendering fallback
        'shape_data'
    )

    # ===========================================================
    # Rotation Configuration
    # ===========================================================
    # 16 steps = 22.5 degrees per step. Good balance for pixel art.
    # Override in subclass if smoother rotation is needed (e.g. 36 for 10 deg).
    ROTATION_STEPS = 16
    ROTATION_INCREMENT = 360 / ROTATION_STEPS

    @staticmethod
    def load_and_scale_image(image_path, scale=1.0, fallback_color=(255, 0, 255)):
        """
        Load image from path and apply scaling.

        Args:
            image_path: Path to image file
            scale: Float or (width_scale, height_scale) tuple
            fallback_color: Color for placeholder if load fails

        Returns:
            pygame.Surface or None if path is None
        """
        if image_path is None:
            return None

        if not os.path.exists(image_path):
            DebugLogger.warn(f"Image not found: {image_path}")
            return None

        try:
            img = pygame.image.load(image_path).convert_alpha()

            # Apply scaling
            if isinstance(scale, (int, float)):
                new_size = (int(img.get_width() * scale),
                            int(img.get_height() * scale))
            elif isinstance(scale, (list, tuple)) and len(scale) == 2:
                new_size = (int(img.get_width() * scale[0]),
                            int(img.get_height() * scale[1]))
            else:
                return img

            return pygame.transform.scale(img, new_size)

        except pygame.error as e:  # Catch specific Pygame errors for corrupted/unsupported files
            DebugLogger.fail(f"Pygame failed to load or process {image_path}: {e}")
            return None
        except Exception as e:  # Catch all other exceptions (e.g., general OS error)
            DebugLogger.fail(f"Failed loading/scaling {image_path}: {e}")
            return None

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, x: float, y: float, image: Optional[pygame.Surface] = None,
                 shape_data: Optional[dict] = None, draw_manager: Optional = None,
                 hitbox_config: Optional[dict] = None,):
        """
        Initialize entity with flexible rendering options.
        """
        # -------------------------------------------------------
        # Core Spatial Attributes
        # -------------------------------------------------------
        self.pos = pygame.Vector2(x, y)

        # -------------------------------------------------------
        # Validation: Prevent API misuse
        # -------------------------------------------------------
        if image is not None and shape_data is not None:
            raise ValueError(
                f"{type(self).__name__}: Cannot provide both 'image' AND 'shape_data'. "
                f"Use one or the other."
            )

        if shape_data and not draw_manager:
            DebugLogger.warn(
                f"{type(self).__name__}: shape_data provided without draw_manager. "
                f"Shape will render per-frame (slow). Pass draw_manager for optimization."
            )

        # Convert shape to image at creation time
        if image is None and shape_data and draw_manager:
            self.image = draw_manager.prebake_shape(
                type=shape_data["type"],
                size=shape_data["size"],
                color=shape_data["color"],
                **shape_data.get("kwargs", {})
            )
            self.shape_data = shape_data
        else:
            self.image = image

        # Store base image for rotation (critical for cache system)
        self._base_image = self.image

        # -------------------------------------------------------
        # Rotation Cache Initialization
        # -------------------------------------------------------
        # Lazy cache: generated on-demand to prevent spawn spikes.
        # Building 16 rotations upfront for 50 bullets = 800 pygame.transform calls (LAG).
        self._rotation_cache = {}  # {angle_index: surface}
        self._cached_rotation_index = -1

        # -------------------------------------------------------
        # Rect Setup (center-aligned)
        # -------------------------------------------------------
        if self.image:
            self.rect = self.image.get_rect(center=(x, y))
        else:
            # Fallback for entities created without draw_manager
            size = shape_data.get("size", (10, 10)) if shape_data else (10, 10)
            self.rect = pygame.Rect(0, 0, *size)
            self.rect.center = (x, y)
            # Store shape config for manual rendering (fallback path)
            self.shape_data = shape_data

        self.draw_manager = draw_manager

        # Rotation Support (optional, used by entities that rotate)
        self.rotation_angle = 0  # Current rotation in degrees
        self._rotation_enabled = False

        # Entity State
        self.death_state = LifecycleState.ALIVE

        # Default layer - subclasses SHOULD override this
        self.layer = Layers.ENEMIES

        # -------------------------------------------------------
        # Attributes
        # -------------------------------------------------------
        self.category = EntityCategory.PARTICLE
        self.collision_tag = "neutral"
        self.tags = set()

        self._current_sprite = None  # Subclasses set initial state
        self._sprite_config = {}  # Subclasses populate state→image/color mapping

        # Animation frame storage (for sprite-cycling animations)
        self._death_frames = []
        self._damage_frames = []
        self.anim_context = {}

        # Initialize animation manager AFTER all attributes exist
        self.anim_manager = AnimationManager(self)

        # -------------------------------------------------------
        # Hitbox Configuration
        # -------------------------------------------------------
        self._setup_hitbox_config(hitbox_config)

    def _setup_hitbox_config(self, hitbox_config):
        """Initialize hitbox configuration from JSON data."""
        if hitbox_config is None:
            hitbox_config = {}

        # Standardized attribute names (no underscore prefix)
        self.hitbox_scale = hitbox_config.get('scale', 0.9)
        self.hitbox_shape = hitbox_config.get('shape', 'rect')
        self.hitbox_offset = hitbox_config.get('offset', (0, 0))
        self.hitbox_params = {k: v for k, v in hitbox_config.items()
                              if k not in ('scale', 'shape', 'offset')}
        self.hitbox = None  # Populated by collision_manager

    # ===========================================================
    # Spatial Synchronization
    # ===========================================================
    def sync_rect(self):
        """
        Synchronize rect.center with self.pos.
        """
        self.rect.centerx = int(self.pos.x)
        self.rect.centery = int(self.pos.y)

    # ===========================================================
    # Core Update Loop
    # ===========================================================
    def update(self, dt: float):
        """
        Update the entity's state for this frame.
        Subclasses MUST override this.
        """
        pass

    def mark_dead(self, immediate=False):
        """
        Mark entity as no longer alive.
        """
        if self.death_state == LifecycleState.DEAD:
            return

        if immediate or self.death_state == LifecycleState.DYING:
            self.death_state = LifecycleState.DEAD
        else:
            self.death_state = LifecycleState.DYING

        DebugLogger.state(
            f"[{type(self).__name__}] → {self.death_state.name}",
            category="entity"
        )

    def reset(self, x, y, **kwargs):
        """
        Reset entity to reusable state (for pooling).
        """
        self.pos.update(x, y)
        self.death_state = LifecycleState.ALIVE

        # Reset Rotation Cache State
        self.rotation_angle = 0
        self._cached_rotation_index = -1

        # FIXED: Always clear cache on reset to prevent stale sprites from previous pool usage.
        # Since we use lazy caching, this is cheap (O(1)) and prevents visual bugs.
        if self._rotation_enabled:
            self._rotation_cache.clear()

        # Restore base image
        if hasattr(self, '_base_image') and self._base_image:
            self.image = self._base_image

        self.sync_rect()

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Queue this entity for rendering via the DrawManager.
        """
        if self.image is not None:
            draw_manager.draw_entity(self, self.layer)
        elif hasattr(self, 'shape_data') and self.shape_data:
            draw_manager.queue_shape(
                self.shape_data["type"],
                self.rect,
                self.shape_data["color"],
                self.layer,
                **self.shape_data.get("kwargs", {})
            )
        else:
            DebugLogger.warn(
                f"{type(self).__name__} has no image or shape_data; drawing debug rect"
            )
            draw_manager.queue_shape(
                "rect",
                self.rect,
                (255, 0, 255),
                self.layer,
                width=1
            )

    def refresh_sprite(self, new_image=None, new_color=None, shape_type=None, size=None):
        """
        Rebuild entity visuals when appearance changes at runtime.
        """
        if new_image:
            self.image = new_image
        elif new_color and hasattr(self, 'shape_data'):
            if not (hasattr(self, 'draw_manager') and self.draw_manager):
                DebugLogger.warn(f"{type(self).__name__} can't rebake - no draw_manager")
                return

            shape_type = shape_type or self.shape_data.get("type", "rect")
            size = size or self.shape_data.get("size", (10, 10))

            if hasattr(self, 'draw_manager') and self.draw_manager:
                self.image = self.draw_manager.prebake_shape(
                    type=shape_type,
                    size=size,
                    color=new_color
                )

        # Update base image and clear rotation cache
        if self.image:
            self._base_image = self.image
            self.rotation_angle = 0

            # CRITICAL: Clear cache because the source image changed
            if self._rotation_enabled:
                self._rotation_cache.clear()
                self._cached_rotation_index = -1

        if self.image:
            self.rect = self.image.get_rect(center=self.pos)

    # ===========================================================
    # Rotation System (Optimized)
    # ===========================================================

    def _get_rotated_surface(self, index):
        """
        Retrieve from cache or generate on demand (Lazy Caching).

        Args:
            index (int): The 0-N index of the rotation step.

        Returns:
            pygame.Surface: The rotated surface.
        """
        # Return cached if available
        if index in self._rotation_cache:
            return self._rotation_cache[index]

        # Guard: No source image
        if not self._base_image:
            return self.image

        # Generate on demand
        angle = index * self.ROTATION_INCREMENT
        rotated_surface = pygame.transform.rotate(self._base_image, angle)

        # Cache it
        self._rotation_cache[index] = rotated_surface

        return rotated_surface

    def update_rotation(self, velocity=None):
        """
        Snap velocity angle to nearest cached step and swap sprite.
        Uses lazy caching to avoid massive CPU spikes on spawn.
        """
        if not self._rotation_enabled or not self._base_image:
            return

        # 1. Determine velocity
        vel = velocity if velocity is not None else getattr(self, 'velocity', None)
        if vel is None or vel.length_squared() < 0.01:
            return

        # 2. Calculate target angle (Assuming sprite faces UP: 0, -1)
        # angle_to calculates angle from self to other
        angle = -pygame.math.Vector2(0, -1).angle_to(vel)

        # 3. Normalize angle to 0-360
        angle = angle % 360

        # 4. Calculate Cache Index (Round to nearest step)
        # Adding 0.5 allows rounding via int truncation
        index = int(round(angle / self.ROTATION_INCREMENT)) % self.ROTATION_STEPS

        # 5. Apply only if index changed (Minimizes rect updates)
        if index != self._cached_rotation_index:
            self.image = self._get_rotated_surface(index)
            self.rect = self.image.get_rect(center=self.rect.center)
            self._cached_rotation_index = index
            self.rotation_angle = index * self.ROTATION_INCREMENT

    # ===========================================================
    # Collision Interface
    # ===========================================================
    def on_collision(self, other: "BaseEntity"):
        pass

    # ===========================================================
    # Utility Methods
    # ===========================================================
    def distance_to(self, other: "BaseEntity") -> float:
        return self.pos.distance_to(other.pos)

    # ===========================================================
    # Bounds & Margin System
    # ===========================================================
    def get_cleanup_margin(self):
        return self._CLEANUP_MARGINS.get(self.category, 200)

    def get_damage_margin(self):
        return self._DAMAGE_MARGINS.get(self.category, 0)

    def is_offscreen(self, margin=None):
        """
        Check if entity is far enough offscreen for cleanup.
        """
        m = margin if margin is not None else self.get_cleanup_margin()
        return (self.rect.right < -m or
                self.rect.left > Display.WIDTH + m or
                self.rect.bottom < -m or
                self.rect.top > Display.HEIGHT + m)

    def is_hittable(self):
        m = self.get_damage_margin()
        return (self.rect.right > m and
                self.rect.left < Display.WIDTH - m and
                self.rect.bottom > m and
                self.rect.top < Display.HEIGHT - m)

    def has_tag(self, tag):
        return tag == self.category or tag in self.tags

    def __repr__(self) -> str:
        return (
            f"<{type(self).__name__} "
            f"pos=({self.pos.x:.1f}, {self.pos.y:.1f}) "
            f"tag={self.collision_tag} "
            f"category={getattr(self, 'category', '?')}>"
        )

    def setup_sprite(self, health, thresholds_dict, color_states, image_states=None, render_mode="shape"):
        # Get all state keys (ordered by threshold, highest first)
        sorted_states = sorted(
            thresholds_dict.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Determine initial state from health
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
        colors = self._sprite_config.get('colors', {})
        return colors.get(self._current_sprite, (255, 255, 255))

    def get_target_color(self, state_key):
        colors = self._sprite_config.get('colors', {})
        return colors.get(state_key, (255, 255, 255))

    def get_current_image(self):
        images = self._sprite_config.get('images', {})
        return images.get(self._current_sprite)

    def get_target_image(self, state_key):
        images = self._sprite_config.get('images', {})
        return images.get(state_key)

    def load_animation_frames(self, frame_paths, scale=1.0):
        frames = []
        for path in frame_paths:
            frame = self.load_and_scale_image(path, scale)
            if frame:
                frames.append(frame)
        return frames
