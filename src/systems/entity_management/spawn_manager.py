"""
spawn_manager.py
----------------
Generic manager responsible for dynamically spawning, updating, and rendering
in-game entities during a scene (enemies, environment objects, pickups, etc.).

Responsibilities
----------------
- Spawn and organize all active entities registered in the EntityRegistry.
- Support scalable updates and cleanup for large numbers of dynamic objects.
- Automatically link new entities to collision systems (if provided).
- Handle per-frame update and render passes for all active entities.
"""
from src.core.debug.debug_logger import DebugLogger
from src.systems.entity_management.entity_registry import EntityRegistry
from src.entities.entity_state import LifecycleState
from src.entities.base_entity import BaseEntity


class SpawnManager:
    """
    Centralized spawner for dynamic scene entities.

    This system manages objects that are created and destroyed during gameplay,
    including enemies, environment props, projectiles, or special effects.
    It handles initialization, updates, rendering, and lifecycle cleanup.
    """

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, draw_manager, display=None, collision_manager=None):
        """
        Initialize the spawn manager and its dependencies.

        Args:
            draw_manager: Global DrawManager used for rendering.
            display (optional): DisplayManager providing viewport info.
            collision_manager (optional): Collision system for hitbox registration.
        """
        self.draw_manager = draw_manager
        self.display = display
        self.collision_manager = collision_manager
        self.entities = []  # Active entities
        self._alive_cache = []  # Cache for alive entities (updated per frame)
        self.on_entity_destroyed = None

        # Pooling system
        self.pools = {}  # {(category, type_name): [inactive_entities]}
        self.pool_enabled = {}  # {(category, type_name): bool}
        self._validated_types = set()

        # Statistics tracking
        self._spawn_stats = {
            "total_spawned": 0,
            "total_failed": 0,
            "pooled_spawns": 0,
            "new_spawns": 0
        }

        DebugLogger.init_entry("SpawnManager Initialized")

    # ===========================================================
    # Cold Validation (runs once per entity type)
    # ===========================================================
    def _validate_entity_type(self, category: str, type_name: str, x: float, y: float) -> bool:
        """
        Validate entity type exists and produces valid entities.
        Called only on first spawn of each type (cold path).

        Returns:
            bool: True if type is valid and can be spawned
        """
        # Check registry
        if not EntityRegistry.has(category, type_name):
            DebugLogger.warn(
                f"Entity not registered: [{category}:{type_name}]. "
                f"Available: {EntityRegistry.get_registered_names(category)}",
                category="entity_spawn"
            )
            self._spawn_stats["total_failed"] += 1
            return False

        # Validate spawn bounds (warning only)
        if self.display:
            width = getattr(self.display, 'game_width', 1280)
            height = getattr(self.display, 'game_height', 720)
            SPAWN_MARGIN = 1000

            if (x < -SPAWN_MARGIN or x > width + SPAWN_MARGIN or
                    y < -SPAWN_MARGIN or y > height + SPAWN_MARGIN):
                DebugLogger.warn(
                    f"Spawn position extreme: [{category}:{type_name}] at ({x:.1f}, {y:.1f})",
                    category="entity_spawn"
                )

        # Create test instance to validate structure
        test_entity = EntityRegistry.create(
            category, type_name, -9999, -9999,
            draw_manager=self.draw_manager
        )

        if not test_entity:
            DebugLogger.warn(
                f"Failed to create test instance for [{category}:{type_name}]",
                category="entity_spawn"
            )
            self._spawn_stats["total_failed"] += 1
            return False

        # Validate required attributes
        missing = []
        if not hasattr(test_entity, 'rect'):
            missing.append('rect')
        if not hasattr(test_entity, 'pos'):
            missing.append('pos')
        if not hasattr(test_entity, 'death_state'):
            missing.append('death_state')
        if not hasattr(test_entity, 'reset'):
            missing.append('reset')

        if missing:
            DebugLogger.warn(
                f"Entity {type(test_entity).__name__} missing attributes: {missing}",
                category="entity_spawn"
            )
            self._spawn_stats["total_failed"] += 1
            return False

        # Cleanup test instance
        if hasattr(test_entity, 'cleanup'):
            test_entity.cleanup()

        DebugLogger.trace(
            f"Validated entity type [{category}:{type_name}]",
            category="entity_spawn"
        )
        return True

    # ===========================================================
    # Entity Spawning
    # ===========================================================
    def spawn(self, category: str, type_name: str, x: float, y: float, **kwargs) -> BaseEntity | None:
        """
        Spawn a new entity and register it with the scene.
        """
        key = (category, type_name)

        if key not in self._validated_types:
            if not self._validate_entity_type(category, type_name, x, y):
                return None
            self._validated_types.add(key)

        kwargs.setdefault("draw_manager", self.draw_manager)

        entity = None
        from_pool = False

        # Try pool first if enabled
        if self.pool_enabled.get(key):
            entity = self._get_from_pool(category, type_name)

            if entity:
                from_pool = True
                try:
                    entity.reset(x, y, **kwargs)
                    # Reset alpha to prevent faded spawns
                    if getattr(entity, 'image', None):
                        entity.image.set_alpha(255)
                except Exception as e:
                    DebugLogger.warn(
                        f"Failed to reset pooled {type(entity).__name__}: {e}",
                        category="entity_spawn"
                    )
                    entity = None
                    from_pool = False

        # Create new if pool miss
        if entity is None:
            entity = EntityRegistry.create(category, type_name, x, y, **kwargs)

            if not entity:
                DebugLogger.warn(
                    f"Failed to instantiate [{category}:{type_name}]",
                    category="entity_spawn"
                )
                self._spawn_stats["total_failed"] += 1
                return None

        # Add to active entities
        self.entities.append(entity)

        # Register hitbox with collision system (type validated, trust entity has hitbox)
        if self.collision_manager:
            try:
                self.collision_manager.register_hitbox(entity)
            except Exception as e:
                DebugLogger.warn(
                    f"Failed to register hitbox for {type(entity).__name__}: {e}",
                    category="entity_spawn"
                )

        # Update statistics
        self._spawn_stats["total_spawned"] += 1
        if from_pool:
            self._spawn_stats["pooled_spawns"] += 1
        else:
            self._spawn_stats["new_spawns"] += 1

        DebugLogger.system(
            f"Spawned {type(entity).__name__} at ({x:.0f}, {y:.0f})",
            category="entity_spawn"
        )

        return entity

    # ===========================================================
    # Pooling System
    # ===========================================================

    def enable_pooling(self, category: str, type_name: str, prewarm_count: int = 20):
        """
        Enable pooling for a specific entity type and optionally prewarm.

        Args:
            category: Entity category (e.g., "enemy")
            type_name: Entity type (e.g., "straight")
            prewarm_count: Number of instances to precreate
        """
        # VALIDATION: Check if entity exists
        if not EntityRegistry.has(category, type_name):
            DebugLogger.warn(
                f"Cannot enable pooling for unregistered entity: [{category}:{type_name}]",
                category="entity_spawn"
            )
            return

        key = (category, type_name)
        self.pool_enabled[key] = True

        if key not in self.pools:
            self.pools[key] = []

        # Prewarm pool
        if prewarm_count > 0:
            self._prewarm_pool(category, type_name, prewarm_count)

        DebugLogger.init_sub(
            f"Enabled [{category}:{type_name}] pooling with {prewarm_count} prewarmed instances"
        )

    def _prewarm_pool(self, category: str, type_name: str, count: int):
        """Create instances ahead of time for pooling."""
        key = (category, type_name)
        created = 0
        failed = 0

        for _ in range(count):
            # Create at offscreen position
            entity = EntityRegistry.create(
                category, type_name, -1000, -1000,
                draw_manager=self.draw_manager
            )
            if entity:
                entity.death_state = LifecycleState.DEAD  # Mark as inactive
                self.pools[key].append(entity)
                created += 1
            else:
                failed += 1

        if failed > 0:
            DebugLogger.warn(
                f"Pool prewarm incomplete for [{category}:{type_name}]: "
                f"{created} created, {failed} failed",
                category="entity_spawn"
            )

    def _get_from_pool(self, category: str, type_name: str):
        """Try to get entity from pool, returns None if pool empty."""
        pool = self.pools.get((category, type_name))
        return pool.pop() if pool else None

    def _return_to_pool(self, entity):
        """Return entity to its pool if pooling is enabled for its type."""
        category = getattr(entity, "category", None)
        type_name = self._get_entity_type_name(entity)

        if not category or not type_name:
            return False

        key = (category, type_name)

        if self.pool_enabled.get(key):
            entity.death_state = LifecycleState.DEAD
            self.pools[key].append(entity)
            return True

        return False

    def _get_entity_type_name(self, entity) -> str:
        """
        Extract type name from entity class name.

        Convention: EnemyStraight -> straight, BulletHoming -> homing
        """
        class_name = type(entity).__name__

        # Strip common prefixes
        for prefix in ["Enemy", "Bullet", "Item", "Pickup", "Obstacle", "Hazard"]:
            if class_name.startswith(prefix):
                return class_name[len(prefix):].lower()

        return class_name.lower()

    # ===========================================================
    # Update Loop
    # ===========================================================
    def update(self, dt: float):
        """
        Update all active entities.

        Args:
            dt (float): Delta time since last frame (in seconds).
        """
        self._alive_cache = [e for e in self.entities if e.death_state < LifecycleState.DEAD]

        for entity in self._alive_cache:
            entity.update(dt)

    # ===========================================================
    # Rendering Pass
    # ===========================================================
    def draw(self):
        """Render all active entities using the global DrawManager."""
        for entity in self._alive_cache:
            entity.draw(self.draw_manager)

    # ===========================================================
    # Cleanup
    # ===========================================================
    def cleanup(self):
        """
        Remove all entities that are marked as DEAD.

        This is typically called after each frame or during major game events
        (e.g., scene reset or stage transition).
        """
        if not self.entities:
            return

        total_before = len(self.entities)
        i = 0
        returned_to_pool = 0
        destroyed = 0

        for entity in self.entities:
            if entity.death_state < LifecycleState.DEAD:
                # Keep alive entities
                self.entities[i] = entity
                i += 1
            else:
                # Entity is dead - process cleanup
                if self.on_entity_destroyed:
                    self.on_entity_destroyed(entity)

                # Call entity's cleanup method if it exists
                if hasattr(entity, 'cleanup'):
                    try:
                        entity.cleanup()
                    except Exception as e:
                        DebugLogger.warn(
                            f"Error during {type(entity).__name__}.cleanup(): {e}",
                            category="entity_cleanup"
                        )

                # Try to return to pool, otherwise it's destroyed
                if self._return_to_pool(entity):
                    returned_to_pool += 1
                else:
                    destroyed += 1

        # Remove dead entities from list
        del self.entities[i:]
        removed = total_before - i

        if removed > 0:
            DebugLogger.state(
                f"Cleaned up {removed} entities ({returned_to_pool} pooled, {destroyed} destroyed)",
                category="entity_cleanup"
            )

    # ===========================================================
    # Query & Statistics
    # ===========================================================

    def get_entities_by_category(self, category):
        """Get all entities matching a specific category."""
        return [e for e in self.entities if getattr(e, "category", None) == category]

    def cleanup_by_category(self, category):
        """Remove all entities of a specific category."""
        before = len(self.entities)
        self.entities = [e for e in self.entities if getattr(e, "category", None) != category]
        removed = before - len(self.entities)

        if removed > 0:
            DebugLogger.state(
                f"Removed {removed} entities of category '{category}'",
                category="entity_cleanup"
            )

    def get_pool_stats(self) -> dict:
        """Return detailed debug info about entity pools."""
        stats = {}
        for (category, type_name), pool in self.pools.items():
            key = f"{category}:{type_name}"
            stats[key] = {
                "available": len(pool),
                "enabled": self.pool_enabled.get((category, type_name), False)
            }
        return stats

    def get_spawn_stats(self) -> dict:
        """
        Get comprehensive spawn system statistics.

        Returns:
            dict: Statistics about active entities, pools, and spawn history
        """
        stats = {
            "active_entities": len(self.entities),
            "entities_by_category": {},
            "lifetime_stats": self._spawn_stats.copy(),
            "pool_stats": self.get_pool_stats()
        }

        # Count entities by category
        for entity in self.entities:
            category = getattr(entity, "category", "unknown")
            stats["entities_by_category"][category] = \
                stats["entities_by_category"].get(category, 0) + 1

        return stats

    def reset_spawn_stats(self):
        """Reset lifetime spawn statistics (useful for level transitions)."""
        self._spawn_stats = {
            "total_spawned": 0,
            "total_failed": 0,
            "pooled_spawns": 0,
            "new_spawns": 0
        }

    # ===========================================================
    # Reset
    # ===========================================================
    def reset(self):
        """
        Completely reset SpawnManager for a new stage/level.
        Marks all entities as dead and returns them to pools.
        """
        for entity in self.entities:
            entity.death_state = LifecycleState.DEAD
            self._return_to_pool(entity)

        self.entities.clear()
        # Note: Keep _validated_types - entity classes don't change between levels
        # Clear only if you want to re-validate (e.g., for hot-reload debugging)
        DebugLogger.system("SpawnManager reset (pools preserved)", category="entity_spawn")
