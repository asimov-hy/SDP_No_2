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

from src.core.utils.debug_logger import DebugLogger
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
        self.entities = []  # Active enemy entities

        DebugLogger.init("Initialized SpawnManager")

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

        entity = EntityRegistry.create(category, type_name, x, y, **kwargs)
        if not entity:
            DebugLogger.warn(f"Failed to spawn {category}: '{type_name}'")
            return
        self.entities.append(entity)

        # Register the enemy’s hitbox
        if self.collision_manager and hasattr(entity, "_hitbox_scale"):
            self.collision_manager.register_hitbox(entity, scale=entity._hitbox_scale)

    # ===========================================================
    # Update Loop
    # ===========================================================
    def update(self, dt: float):
        """
        Update all active entities and remove inactive ones.

        Args:
            dt (float): Delta time since last frame (in seconds).
        """
        if not self.entities:
            return

        # Update positions and hitboxes before collision checks
        for entity in self.entities:
            if entity.death_state >= LifecycleState.DEAD:
                continue
            entity.update(dt)

        # Efficient cleanup of inactive or destroyed entities
        i = 0
        total_before = len(self.entities)
        for e in self.entities:
            if e.death_state < LifecycleState.DEAD:
                self.entities[i] = e
                i += 1
        del self.entities[i:]

        removed = total_before - i
        if removed > 0:
            DebugLogger.state(
                f"Removed {removed} inactive entities",
                category="entity"
            )

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
        Immediately remove all entities that are no longer alive.

        This is typically called after a major game event (e.g., scene reset
        or stage transition) to clear destroyed or expired objects.
        """
        total_before = len(self.entities)
        i = 0
        for e in self.entities:
            if e.death_state < LifecycleState.DEAD:
                self.entities[i] = e
                i += 1
        del self.entities[i:]

        removed = total_before - i
        if removed > 0:
            DebugLogger.state(
                f"Cleaned up {removed} destroyed entities",
                category="entity_cleanup"
            )

    # ===========================================================
    # Helpers
    # ===========================================================

    def get_entities_by_category(self, category):
        return [e for e in self.entities if getattr(e, "category", None) == category]

    def cleanup_by_category(self, category):
        self.entities = [e for e in self.entities if getattr(e, "category", None) != category]


