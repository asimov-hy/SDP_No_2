"""
collision_manager.py
--------------------
Optimized modular collision handler with centralized hitbox management.
Uses spatial hashing to reduce redundant collision checks
and delegates actual responses to entities_animation and bullets.

Responsibilities
----------------
- Manage hitbox lifecycle for all entities_animation (registration, updates, cleanup).
- Detect collisions between bullets ↔ entities_animation using spatial hashing.
- Delegate collision responses to entity.on_collision() methods.
- Support collision rules for flexible filtering.
- Provide optional hitbox debug visualization.
"""

import pygame
from src.core.runtime.game_settings import Debug
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState
from src.entities.entity_state import InteractionState
from src.systems.collision.collision_hitbox import CollisionHitbox
from src.core.runtime.game_settings import Display


class CollisionManager:
    """Detects collisions but lets objects decide what happens."""

    BASE_CELL_SIZE = 64
    NEIGHBOR_OFFSETS = [
        (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (-1, 1), (1, -1), (-1, -1)
    ]

    def __init__(self, player, bullet_manager, spawn_manager):
        self.player = player
        self.bullet_manager = bullet_manager
        self.spawn_manager = spawn_manager
        self.CELL_SIZE = self.BASE_CELL_SIZE

        self.rules = {
            ("player", "enemy"),
            ("player", "pickup"),
            ("player_bullet", "enemy"),
            ("enemy_bullet", "player"),
            ("player_bullet", "enemy_bullet"),
        }

        self.hitboxes = {}
        self._collisions = []
        self._checked_pairs = set()

        self._entity_cache = {}

        # [OPTIMIZATION] Pre-allocated 1D spatial grid
        self.GRID_COLS = (Display.WIDTH + self.CELL_SIZE * 2) // self.CELL_SIZE + 1
        self.GRID_ROWS = (Display.HEIGHT + self.CELL_SIZE * 2) // self.CELL_SIZE + 1
        self.TOTAL_CELLS = self.GRID_COLS * self.GRID_ROWS
        self._grid = [[] for _ in range(self.TOTAL_CELLS)]

        DebugLogger.init_entry("CollisionManager Initialized")

    # ===========================================================
    # Hitbox Lifecycle Management
    # ===========================================================
    def register_hitbox(self, entity, scale=None, offset=(0, 0), shape=None, shape_params=None):
        """Create and register a hitbox for an entity."""
        # Extract from entity if not provided (allows overrides)
        scale = scale if scale is not None else getattr(entity, 'hitbox_scale', 1.0)
        shape = shape if shape is not None else getattr(entity, 'hitbox_shape', 'rect')
        shape_params = shape_params if shape_params is not None else getattr(entity, 'hitbox_params', {})

        hitbox = CollisionHitbox(entity, scale=scale, offset=offset,
                                 shape=shape, shape_params=shape_params)

        self.hitboxes[id(entity)] = hitbox
        entity.hitbox = hitbox  # Store back-reference

        # Cache frequently-accessed attributes for hot path optimization
        entity_id = id(entity)
        self._entity_cache[entity_id] = {
            "collision_tag": getattr(entity, "collision_tag", None),
        }

        DebugLogger.trace(f"Registered hitbox for {type(entity).__name__}")
        return hitbox

    def unregister_hitbox(self, entity):
        """Remove hitbox when entity is destroyed."""
        entity_id = id(entity)
        if entity_id in self.hitboxes:
            del self.hitboxes[entity_id]
            # Clean cache entry
            self._entity_cache.pop(entity_id, None)
            DebugLogger.trace(f"Unregistered hitbox for {type(entity).__name__}")

    def get_hitbox(self, entity):
        """Get the hitbox for an entity."""
        return self.hitboxes.get(id(entity))

    def update(self):
        """
        Update all registered hitboxes to match entity positions.
        Automatically cleans up hitboxes for dead entities.
        """
        for hitbox in self.hitboxes.values():
            # Trust that dead entities have been unregistered
            # Update hitbox position/size
            hitbox.update()

    # ===========================================================
    # Utility: Grid Assignment
    # ===========================================================
    def _add_to_grid(self, obj):
        """
        [OPTIMIZATION] Assign entity to 1D grid using offset coordinates.

        Grid coordinate system:
        - Logical grid origin is at (-CELL_SIZE, -CELL_SIZE)
        - This allows entities at negative positions (off-screen spawns)
        - Adding CELL_SIZE shifts coordinates into positive range
        """
        hitbox = self.hitboxes.get(id(obj))
        if not hitbox:
            return

        rect = hitbox.rect

        # [CRITICAL] Add CELL_SIZE offset to handle negative coordinates
        start_x = int((rect.left + self.CELL_SIZE) // self.CELL_SIZE)
        end_x = int((rect.right + self.CELL_SIZE) // self.CELL_SIZE)
        start_y = int((rect.top + self.CELL_SIZE) // self.CELL_SIZE)
        end_y = int((rect.bottom + self.CELL_SIZE) // self.CELL_SIZE)

        max_col = self.GRID_COLS - 1
        max_row = self.GRID_ROWS - 1

        for cx in range(start_x, end_x + 1):
            for cy in range(start_y, end_y + 1):
                if 0 <= cx <= max_col and 0 <= cy <= max_row:
                    index = cx + cy * self.GRID_COLS
                    self._grid[index].append(obj)

    # ===========================================================
    # Optimized Collision Detection
    # ===========================================================
    def detect(self):
        """[OPTIMIZED] Collision detection using fixed-array spatial hashing."""
        self._collisions.clear()

        # [OPTIMIZATION] Clear buckets without reallocation
        for bucket in self._grid:
            bucket.clear()

        self._checked_pairs.clear()

        # Broad-phase culling
        margin = 150
        collision_bounds = pygame.Rect(-margin, -margin,
                                       Display.WIDTH + margin * 2,
                                       Display.HEIGHT + margin * 2)

        # Filter active entities
        active_bullets = [
            b for b in self.bullet_manager.active
            if collision_bounds.collidepoint(b.pos)
        ]

        active_entities = [
            e for e in self.spawn_manager.entities
            if collision_bounds.collidepoint(e.pos)
        ]

        # Cache player alive check
        player = None
        if self.player and self.player.death_state < LifecycleState.DEAD:
            player = self.player

        total_entities = len(active_bullets) + len(active_entities) + (1 if player else 0)

        if total_entities == 0:
            return self._collisions

        # Build spatial grid
        add_to_grid = self._add_to_grid

        if player:
            add_to_grid(player)
        for entity in active_entities:
            if entity is not player:
                add_to_grid(entity)
        for bullet in active_bullets:
            add_to_grid(bullet)

        # Collision detection
        append_collision = self._collisions.append
        get_hitbox = self.hitboxes.get
        checked_pairs = self._checked_pairs

        for index in range(self.TOTAL_CELLS):
            cell_objects = self._grid[index]
            if not cell_objects:
                continue

            cx = index % self.GRID_COLS
            cy = index // self.GRID_COLS

            for dx, dy in self.NEIGHBOR_OFFSETS:
                neighbor_x = cx + dx
                neighbor_y = cy + dy

                if not (0 <= neighbor_x < self.GRID_COLS and
                        0 <= neighbor_y < self.GRID_ROWS):
                    continue

                neighbor_index = neighbor_x + neighbor_y * self.GRID_COLS
                neighbor_objs = self._grid[neighbor_index]

                for a in cell_objects:
                    a_id = id(a)
                    a_hitbox = get_hitbox(a_id)
                    if not a_hitbox or not a_hitbox.active:
                        continue

                    a_cache = self._entity_cache.get(a_id, {})
                    a_tag = a_cache.get("collision_tag")

                    for b in neighbor_objs:
                        if a is b:
                            continue

                        b_id = id(b)
                        pair_key = (a_id, b_id) if a_id < b_id else (b_id, a_id)

                        if pair_key in checked_pairs:
                            continue
                        checked_pairs.add(pair_key)

                        b_hitbox = get_hitbox(b_id)
                        if not b_hitbox or not b_hitbox.active:
                            continue

                        b_cache = self._entity_cache.get(b_id, {})
                        b_tag = b_cache.get("collision_tag")

                        if (a_tag, b_tag) not in self.rules and (b_tag, a_tag) not in self.rules:
                            continue

                        # Check state if entities have it (some entities like items may not)
                        a_state = getattr(a, 'state', InteractionState.DEFAULT)
                        b_state = getattr(b, 'state', InteractionState.DEFAULT)

                        if a_state >= InteractionState.INTANGIBLE or b_state >= InteractionState.INTANGIBLE:
                            continue

                        if self._check_collision(a_hitbox, b_hitbox):

                            append_collision((a, b))
                            self._process_collision(a, b)

        return self._collisions

    # ===========================================================
    # Collision Processing
    # ===========================================================
    def _process_collision(self, entity_a, entity_b):
        """Route collision based on categories."""
        try:
            if hasattr(entity_a, "on_collision"):
                entity_a.on_collision(entity_b)

            if hasattr(entity_b, "on_collision"):
                entity_b.on_collision(entity_a)

        except Exception as e:
            DebugLogger.warn(
                f"[Collision] Error {type(entity_a).__name__} <-> {type(entity_b).__name__}: {e}",
                category="collision"
            )

    def _check_collision(self, hitbox_a, hitbox_b):
        """Check collision between two hitboxes (AABB or OBB)."""
        if not hitbox_a.use_obb and not hitbox_b.use_obb:
            return hitbox_a.rect.colliderect(hitbox_b.rect)
        return self._obb_collision(hitbox_a, hitbox_b)

    def _obb_collision(self, hitbox_a, hitbox_b):
        """SAT collision check for oriented bounding boxes."""
        corners_a = hitbox_a.get_obb_corners()
        corners_b = hitbox_b.get_obb_corners()

        # Collect axes from both shapes
        axes = []
        for i in range(len(corners_a)):
            p1 = corners_a[i]
            p2 = corners_a[(i + 1) % len(corners_a)]
            edge = (p2[0] - p1[0], p2[1] - p1[1])
            axes.append((-edge[1], edge[0])) # Normal

        for i in range(len(corners_b)):
            p1 = corners_b[i]
            p2 = corners_b[(i + 1) % len(corners_b)]
            edge = (p2[0] - p1[0], p2[1] - p1[1])
            axes.append((-edge[1], edge[0]))

        # Project and check overlap
        for axis in axes:
            # Normalize axis (optional but good for stability)
            length = (axis[0]**2 + axis[1]**2)**0.5
            if length == 0: continue
            axis = (axis[0]/length, axis[1]/length)

            # Project A
            proj_a = [c[0]*axis[0] + c[1]*axis[1] for c in corners_a]
            min_a, max_a = min(proj_a), max(proj_a)

            # Project B
            proj_b = [c[0]*axis[0] + c[1]*axis[1] for c in corners_b]
            min_b, max_b = min(proj_b), max(proj_b)

            if max_a < min_b or max_b < min_a:
                return False # Gap found

        return True

    # ===========================================================
    # Debug Visualization
    # ===========================================================
    def draw_debug(self, surface):
        """Draw hitboxes if debug enabled."""
        if not Debug.HITBOX_VISIBLE:
            return

        for hitbox in self.hitboxes.values():
            if hitbox.active:
                hitbox.draw_debug(surface)
