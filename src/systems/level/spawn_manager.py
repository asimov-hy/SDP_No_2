"""
spawn_manager.py
----------------
Generic manager responsible for dynamically spawning, updating, and rendering
in-game entities_animation during a scene (enemies, environment objects, pickups, etc.).

Responsibilities
----------------
- Spawn and organize all active entities_animation registered in the EntityRegistry.
- Support scalable updates and cleanup for large numbers of dynamic objects.
- Automatically link new entities_animation to collision systems (if provided).
- Handle per-frame update and render passes for all active entities_animation.
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.enemies.enemy_straight import EnemyStraight
from src.entities.entity_registry import EntityRegistry
from src.entities.entity_state import LifecycleState


# ===========================================================
# Enemy Type Registry
# ===========================================================
ENEMY_TYPES = {
    "straight": EnemyStraight,
    # future types:
    # "zigzag": EnemyZigzag,
    # "shooter": EnemyShooter,
}


class SpawnManager:
    """
    Centralized spawner for dynamic scene entities_animation.

    This system manages objects that are created and destroyed during gameplay,
    including enemies, environment props, projectiles, or special animation_effects.
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
        self.entities = []  # Active enemy entities_animation
        self.on_entity_destroyed = None

        DebugLogger.init_entry("SpawnManager Initialized")

        self.pools = {}  # {(category, type_name): [inactive_entities]}
        self.pool_enabled = {}  # {(category, type_name): bool}

    # ===========================================================
    # Entity Spawning
    # ===========================================================
    def spawn(self, category: str, type_name: str, x: float, y: float, **kwargs):
        """
        Spawn a new entity and register it with the scene.

        Args:
            category (str): Entity group in the registry (e.g., "enemy", "environment").
            type_name (str): Entity type key (e.g., "straight", "asteroid").
            x (float): Spawn x-coordinate.
            y (float): Spawn y-coordinate.
            **kwargs: Additional initialization parameters for the entity.
        """
        kwargs.setdefault("draw_manager", self.draw_manager)

        key = (category, type_name)
        entity = None

        # Try pool first if enabled
        if key in self.pool_enabled and self.pool_enabled[key]:
            entity = self._get_from_pool(category, type_name)

            if entity:
                # Reset pooled entity
                if hasattr(entity, "reset"):
                    entity.reset(x, y, **kwargs)
                else:
                    DebugLogger.warn(f"{type(entity).__name__} missing reset() method")
                    entity = None  # Fallback to creation

        # Create new if pool miss
        if entity is None:
            entity = EntityRegistry.create(category, type_name, x, y, **kwargs)

            if not entity:
                # DebugLogger.warn(f"Failed to spawn {category}: '{type_name}'")
                return None

        DebugLogger.system(f"Spawned {type(entity).__name__} ID: {id(entity)}", category="entity")

        self.entities.append(entity)

        # Register hitbox
        if self.collision_manager and hasattr(entity, "_hitbox_scale"):
            self.collision_manager.register_hitbox(entity, scale=entity._hitbox_scale)

        return entity

    # ===========================================================
    # Pooling Managers
    # ===========================================================

    def enable_pooling(self, category: str, type_name: str, prewarm_count: int = 20):
        """
        Enable pooling for a specific entity type and optionally prewarm.

        Args:
            category: Entity category (e.g., "enemy")
            type_name: Entity type (e.g., "straight")
            prewarm_count: Number of instances to precreate
        """
        key = (category, type_name)
        self.pool_enabled[key] = True

        if key not in self.pools:
            self.pools[key] = []

        # Prewarm pool
        if prewarm_count > 0:
            self._prewarm_pool(category, type_name, prewarm_count)

        DebugLogger.init_sub(f"Enabled [{category}:{type_name}] pooling: {prewarm_count}")

    def _prewarm_pool(self, category: str, type_name: str, count: int):
        """Create instances ahead of time."""
        key = (category, type_name)

        for _ in range(count):
            # Create at offscreen position
            entity = EntityRegistry.create(category, type_name, -1000, -1000,
                                           draw_manager=self.draw_manager)
            if entity:
                entity.death_state = LifecycleState.DEAD  # Mark as inactive
                self.pools[key].append(entity)

    def _get_from_pool(self, category: str, type_name: str):
        """Try to get entity from pool, returns None if pool empty."""
        key = (category, type_name)

        if key not in self.pools or not self.pools[key]:
            return None

        return self.pools[key].pop()

    def _return_to_pool(self, entity):
        """Return entity to its pool."""
        category = getattr(entity, "category", None)
        type_name = self._get_entity_type_name(entity)

        if not category or not type_name:
            return False

        key = (category, type_name)

        if key in self.pool_enabled and self.pool_enabled[key]:
            entity.death_state = LifecycleState.DEAD
            self.pools[key].append(entity)
            return True

        return False

    def _get_entity_type_name(self, entity) -> str:
        """Extract type name from entity class (e.g., EnemyStraight -> straight)."""
        class_name = type(entity).__name__

        # Convention: EnemyStraight -> straight, EnemyZigzag -> zigzag
        if class_name.startswith("Enemy"):
            return class_name[5:].lower()  # Remove "Enemy" prefix

        return class_name.lower()

    # ===========================================================
    # Update Loop
    # ===========================================================
    def update(self, dt: float):
        """
        Update all active entities_animation and remove inactive ones.

        Args:
            dt (float): Delta time since last frame (in seconds).
        """
        if not self.entities:
            return

        # Update positions and hitboxes before collision checks
        for entity in self.entities:
            if entity.death_state < LifecycleState.DEAD:
                entity.update(dt)

    # ===========================================================
    # Rendering Pass
    # ===========================================================
    def draw(self):
        """
        Render all active enemies using the global DrawManager.
        """
        for e in self.entities:
            e.draw(self.draw_manager)

    # ===========================================================
    # Cleanup
    # ===========================================================
    def cleanup(self):
        """
        Immediately remove all entities_animation that are no longer alive.

        This is typically called after a major game event (e.g., scene reset
        or stage transition) to clear destroyed or expired objects.
        """
        if not self.entities:  # Early exit
            return

        total_before = len(self.entities)
        i = 0
        returned_to_pool = 0

        for e in self.entities:
            if e.death_state < LifecycleState.DEAD:
                self.entities[i] = e
                i += 1
            else:
                # Try to return to pool
                if self.on_entity_destroyed:
                    self.on_entity_destroyed(e)

                if self._return_to_pool(e):
                    returned_to_pool += 1

        del self.entities[i:]
        removed = total_before - i

        if removed > 0:
            DebugLogger.state(
                f"Cleaned up {removed} entities_animation ({returned_to_pool} pooled)",
                category="entity_cleanup"
            )

    # ===========================================================
    # Helpers
    # ===========================================================

    def get_entities_by_category(self, category):
        return [e for e in self.entities if getattr(e, "category", None) == category]

    def cleanup_by_category(self, category):
        self.entities = [e for e in self.entities if getattr(e, "category", None) != category]

    def get_pool_stats(self) -> dict:
        """Return simple debug info about current entity pools."""
        stats = {}
        for (category, type_name), pool in self.pools.items():
            stats[f"{category}:{type_name}"] = {
                "available": len(pool),
                "enabled": self.pool_enabled.get((category, type_name), False)
            }
        return stats

    def reset(self):
        """
        Completely reset SpawnManager for a new stage.
        Clears all active entities_animation and pool data.
        """
        for e in self.entities:
            e.death_state = LifecycleState.DEAD
            self._return_to_pool(e)

        self.entities.clear()
        DebugLogger.system("SpawnManager reset (pools preserved)")