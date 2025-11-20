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

    # ===========================================================
    # Configuration
    # ===========================================================
    BASE_CELL_SIZE = 64
    NEIGHBOR_OFFSETS = [
        (0, 0), (1, 0), (-1, 0), (0, 1), (0, -1),
        (1, 1), (-1, 1), (1, -1), (-1, -1)
    ]

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, player, bullet_manager, spawn_manager):
        """
        Initialize the collision manager and register key systems.
        """
        self.player = player
        self.bullet_manager = bullet_manager
        self.spawn_manager = spawn_manager
        self.CELL_SIZE = self.BASE_CELL_SIZE

        # Collision rules
        self.rules = {
            ("player", "enemy"),
            ("player", "pickup"),
            ("player_bullet", "enemy"),
            ("enemy_bullet", "player"),
            ("player_bullet", "enemy_bullet"),
            ("player", "pickup")
        }

        # Centralized hitbox registry
        self.hitboxes = {}  # {entity_id: CollisionHitbox}

        # Reuse structures
        self._collisions = []
        self._grid = {}
        self._checked_pairs = set()

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

        DebugLogger.trace(f"Registered hitbox for {type(entity).__name__}")
        return hitbox

    def unregister_hitbox(self, entity):
        """Remove hitbox when entity is destroyed."""
        entity_id = id(entity)
        if entity_id in self.hitboxes:
            del self.hitboxes[entity_id]
            DebugLogger.trace(f"Unregistered hitbox for {type(entity).__name__}")

    def get_hitbox(self, entity):
        """Get the hitbox for an entity."""
        return self.hitboxes.get(id(entity))

    def update(self):
        """
        Update all registered hitboxes to match entity positions.
        Automatically cleans up hitboxes for dead entities.
        """
        for entity_id, hitbox in list(self.hitboxes.items()):
            # Clean up hitboxes for dead entities
            entity = hitbox.owner
            if getattr(entity, "death_state", 0) >= LifecycleState.DEAD:
                del self.hitboxes[entity_id]
                continue

            # Update hitbox position/size
            hitbox.update()

    # ===========================================================
    # Utility: Grid Assignment
    # ===========================================================
    def _add_to_grid(self, grid, obj):
        """Assign an entity to a grid cell based on its hitbox."""
        hitbox = self.hitboxes.get(id(obj))
        if not hitbox:
            return

        rect = hitbox.rect
        start_x = int(rect.left // self.CELL_SIZE)
        end_x   = int(rect.right // self.CELL_SIZE)
        start_y = int(rect.top // self.CELL_SIZE)
        end_y   = int(rect.bottom // self.CELL_SIZE)

        for cx in range(start_x, end_x + 1):
            for cy in range(start_y, end_y + 1):
                grid.setdefault((cx, cy), []).append(obj)

    # ===========================================================
    # Optimized Collision Detection
    # ===========================================================
    def detect(self):
        """
        Optimized collision detection using spatial hashing with broad-phase culling.
        """
        # Reuse persistent structures
        self._collisions.clear()
        self._grid.clear()
        self._checked_pairs.clear()

        collisions = self._collisions

        # Broad-phase culling bounds
        margin = 150
        collision_bounds = pygame.Rect(-margin, -margin,
                                       Display.WIDTH + margin * 2,
                                       Display.HEIGHT + margin * 2)

        DEAD = LifecycleState.DEAD

        # Single-pass filtering: Alive AND On-Screen
        active_bullets = [
            b for b in getattr(self.bullet_manager, "active", [])
            if getattr(b, "death_state", 0) < DEAD
               and collision_bounds.collidepoint(b.pos)
        ]

        active_entities = [
            e for e in getattr(self.spawn_manager, "entities", [])
            if getattr(e, "death_state", 0) < DEAD
               and collision_bounds.collidepoint(e.pos)
        ]

        player = self.player if getattr(self.player, "death_state", 0) < DEAD else None

        total_entities = len(active_bullets) + len(active_entities) + (1 if player else 0)
        if total_entities == 0:
            return collisions

        # Dynamic grid size adjustment
        if total_entities > 800:
            self.CELL_SIZE = 48
        elif total_entities < 100:
            self.CELL_SIZE = 96
        else:
            self.CELL_SIZE = self.BASE_CELL_SIZE

        # Build Spatial Grid
        add_to_grid = self._add_to_grid
        grid = self._grid

        if player:
            add_to_grid(grid, player)
        for entity in active_entities:
            if entity is player:
                continue
            add_to_grid(grid, entity)
        for bullet in active_bullets:
            add_to_grid(grid, bullet)

        # Localized Collision Checks
        append_collision = collisions.append
        get_hitbox = self.hitboxes.get
        checked_pairs = self._checked_pairs

        for cell_key, cell_objects in grid.items():
            cx, cy = cell_key
            for dx, dy in self.NEIGHBOR_OFFSETS:
                neighbor_key = (cx + dx, cy + dy)
                try:
                    neighbor_objs = grid[neighbor_key]
                except KeyError:
                    continue

                for a in cell_objects:
                    a_id = id(a)
                    a_hitbox = get_hitbox(a_id)
                    if not a_hitbox or not getattr(a_hitbox, "active", True):
                        continue

                    a_tag = getattr(a, "collision_tag", None)

                    for b in neighbor_objs:
                        if a is b:
                            continue

                        b_id = id(b)

                        # OPTIMIZATION: Use cached IDs for pair key
                        if a_id < b_id:
                            pair_key = (a_id, b_id)
                        else:
                            pair_key = (b_id, a_id)

                        if pair_key in checked_pairs:
                            continue
                        checked_pairs.add(pair_key)

                        b_hitbox = get_hitbox(b_id)
                        if not b_hitbox or not getattr(b_hitbox, "active", True):
                            continue

                        # Skip destroyed entities mid-frame
                        if a.death_state >= DEAD or b.death_state >= DEAD:
                            continue

                        # Tag-based filtering
                        b_tag = getattr(b, "collision_tag", None)
                        if (a_tag, b_tag) not in self.rules and (b_tag, a_tag) not in self.rules:
                            continue

                        # State checks (Intangible)
                        a_state = getattr(a, "state", 0)
                        b_state = getattr(b, "state", 0)
                        if a_state >= InteractionState.INTANGIBLE or b_state >= InteractionState.INTANGIBLE:
                            continue

                        # Narrow Phase: Hitbox Overlap
                        if self._check_collision(a_hitbox, b_hitbox):
                            # Hittable zone check
                            a_hittable = not hasattr(a, "is_hittable") or a.is_hittable()
                            b_hittable = not hasattr(b, "is_hittable") or b.is_hittable()

                            if not (a_hittable and b_hittable):
                                continue

                            append_collision((a, b))
                            # process collision immediately
                            self._process_collision(a, b)

        return collisions

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
            if getattr(hitbox, "active", True):
                hitbox.draw_debug(surface)