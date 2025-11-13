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

from src.core.runtime.game_settings import Debug
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState
from src.entities.player.player_state import InteractionState
from src.systems.collision.collision_hitbox import CollisionHitbox


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

        Args:
            player: Player entity instance to include in collision checks.
            bullet_manager: Reference to the BulletManager containing active bullets.
            spawn_manager: Reference to the SpawnManager containing active enemies.
        """
        self.player = player
        self.bullet_manager = bullet_manager
        self.spawn_manager = spawn_manager
        self.CELL_SIZE = self.BASE_CELL_SIZE

        # Collision rules
        self.rules = {
            ("player", "enemy"),
            ("player_bullet", "enemy"),
            ("enemy_bullet", "player"),
            ("player_bullet", "enemy_bullet"),
        }

        # Centralized hitbox registry
        self.hitboxes = {}  # {entity_id: CollisionHitbox}

        DebugLogger.init_entry("CollisionManager Initialized")

    # ===========================================================
    # Hitbox Lifecycle Management
    # ===========================================================
    def register_hitbox(self, entity, scale=1.0, size=None, offset=(0, 0)):
        """
        Create and register a hitbox for an entity.

        Args:
            entity: The entity to create a hitbox for.
            scale: Scale factor relative to entity.rect (default: 1.0).
            size: Explicit (width, height) tuple, overrides scale if provided.
            offset: (x, y) offset from entity center in pixels.

        Returns:
            CollisionHitbox: The created hitbox instance.
        """

        # Create hitbox with scale
        hitbox = CollisionHitbox(entity, scale=scale, offset=offset)

        # Override with explicit size if provided (switches to manual mode)
        if size:
            hitbox.set_size(*size)

        # Register in centralized registry
        self.hitboxes[id(entity)] = hitbox

        DebugLogger.trace(f"Registered hitbox for {type(entity).__name__}")
        return hitbox

    def unregister_hitbox(self, entity):
        """
        Remove hitbox when entity is destroyed.

        Args:
            entity: The entity whose hitbox to remove.
        """
        entity_id = id(entity)
        if entity_id in self.hitboxes:
            del self.hitboxes[entity_id]
            DebugLogger.trace(f"Unregistered hitbox for {type(entity).__name__}")

    def get_hitbox(self, entity):
        """
        Get the hitbox for an entity.

        Args:
            entity: The entity to get hitbox for.

        Returns:
            CollisionHitbox or None if not registered.
        """
        return self.hitboxes.get(id(entity))

    def update(self):
        """
        Update all registered hitboxes to match entity positions.
        Automatically cleans up hitboxes for dead entities_animation.
        """
        for entity_id, hitbox in list(self.hitboxes.items()):
            # Clean up hitboxes for dead entities_animation
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
        """
        Assign an entity to a grid cell based on its hitbox.

        Args:
            grid: Spatial hash table mapping cell → list of entities_animation.
            obj: Any entity with a registered hitbox.
        """
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
        Optimized collision detection using spatial hashing.

        Groups entities_animation by screen regions to minimize redundant checks.
        Delegates all responses to each entity's on_collision() method.

        Returns:
            list[tuple]: List of (object_a, object_b) pairs that have collided.
        """

        collisions = []

        # Pre-filter active objects
        active_bullets = [
            b for b in getattr(self.bullet_manager, "active", [])
            if getattr(b, "death_state", 0) < LifecycleState.DEAD
        ]
        active_entities = [
            e for e in getattr(self.spawn_manager, "entities", [])
            if getattr(e, "death_state", 0) < LifecycleState.DEAD
        ]
        player = self.player if getattr(self.player, "death_state", 0) < LifecycleState.DEAD else None

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
        grid = {}
        add_to_grid = self._add_to_grid

        if player:
            add_to_grid(grid, player)
        for entity in active_entities:
            if entity is player:
                DebugLogger.warn("WARNING: Player found in spawn_manager entities!")
                continue
            add_to_grid(grid, entity)

        for bullet in active_bullets:
            add_to_grid(grid, bullet)

        # Localized Collision Checks (per cell + neighbors)
        checked_pairs = set()
        append_collision = collisions.append
        get_hitbox = self.hitboxes.get

        for cell_key, cell_objects in grid.items():
            for dx, dy in self.NEIGHBOR_OFFSETS:
                neighbor_key = (cell_key[0] + dx, cell_key[1] + dy)
                neighbor_objs = grid.get(neighbor_key)
                if not neighbor_objs:
                    continue

                for a in cell_objects:
                    a_hitbox = get_hitbox(id(a))
                    if not a_hitbox or not getattr(a_hitbox, "active", True):
                        continue

                    for b in neighbor_objs:
                        if a is b:
                            continue

                        b_hitbox = get_hitbox(id(b))
                        if not b_hitbox or not getattr(b_hitbox, "active", True):
                            continue

                        # Avoid redundant duplicate checks
                        pair_key = tuple(sorted((id(a), id(b))))
                        if pair_key in checked_pairs:
                            continue
                        checked_pairs.add(pair_key)

                        # Skip destroyed entities_animation mid-frame
                        if a.death_state >= LifecycleState.DEAD or b.death_state >= LifecycleState.DEAD:
                            continue

                        # Tag-based collision filtering
                        tag_a = getattr(a, "collision_tag", None)
                        tag_b = getattr(b, "collision_tag", None)
                        if (tag_a, tag_b) not in self.rules and (tag_b, tag_a) not in self.rules:
                            continue

                        if (getattr(a, "state", 0) >= InteractionState.INTANGIBLE or
                                getattr(b, "state", 0) >= InteractionState.INTANGIBLE):
                            continue

                        # Overlap test
                        if a_hitbox.rect.colliderect(b_hitbox.rect):
                            append_collision((a, b))
                            DebugLogger.state(
                                f"Collision: {type(a).__name__} ({tag_a}) <-> {type(b).__name__} ({tag_b})",
                                category="collision",
                            )

                            # Let entities_animation handle their reactions
                            try:
                                if hasattr(a, "on_collision"):
                                    a.on_collision(b)

                                if hasattr(b, "on_collision"):
                                    b.on_collision(a)

                            except Exception as e:
                                DebugLogger.warn(
                                    f"[CollisionManager] Exception during collision between "
                                    f"{type(a).__name__} and {type(b).__name__}: {e}",
                                    category="collision"
                                )
        return collisions

    # ===========================================================
    # Debug Visualization
    # ===========================================================
    def draw_debug(self, surface):
        """
        Draw hitboxes for all registered entities_animation if debug mode is enabled.

        Args:
            surface: The rendering surface to draw onto.
        """
        if not Debug.HITBOX_VISIBLE:
            return

        # Draw all registered hitboxes
        for hitbox in self.hitboxes.values():
            if getattr(hitbox, "active", True):
                hitbox.draw_debug(surface)