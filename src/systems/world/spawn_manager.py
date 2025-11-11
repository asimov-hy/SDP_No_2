"""
spawn_manager.py
----------------
Manages the creation, updating, and rendering of enemy entities.

Responsibilities
----------------
- Spawn and organize all active enemy entities.
- Support scalable spawning and cleanup for multiple enemies.
- Handle update and render passes for all active enemies.
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
    """Central manager responsible for enemy spawning, updates, and rendering."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, draw_manager, display=None, collision_manager=None):
        """
        Initialize the spawn manager and enemy registry.

        Args:
            draw_manager: Global DrawManager for rendering.
            display (optional): DisplayManager for screen info (future use).
        """
        self.draw_manager = draw_manager
        self.display = display
        self.collision_manager = collision_manager
        self.enemies = []  # Active enemy entities

        DebugLogger.init("Enemy spawn system initialized")

    # ===========================================================
    # Enemy Spawning
    # ===========================================================
    def spawn_enemy(self, type_name: str, x: float, y: float, **kwargs):
        kwargs.setdefault("draw_manager", self.draw_manager)
        enemy = EntityRegistry.create("enemy", type_name, x, y, **kwargs)
        if not enemy:
            DebugLogger.warn(f"Failed to spawn enemy '{type_name}' via registry")
            return
        self.enemies.append(enemy)

        # Register the enemy’s hitbox
        if self.collision_manager:
            self.collision_manager.register_hitbox(enemy, scale=enemy._hitbox_scale)

    # ===========================================================
    # Update Loop
    # ===========================================================
    def update(self, dt: float):
        """
        Update all active enemies and remove inactive ones.

        Args:
            dt (float): Delta time since last frame (in seconds).
        """
        if not self.enemies:
            return

        # Update positions and hitboxes before collision checks
        for enemy in self.enemies:
            if enemy.death_state >= LifecycleState.DEAD:
                continue
            enemy.update(dt)

        # -------------------------------------------------------
        # Cleanup inactive enemies efficiently
        # -------------------------------------------------------
        i = 0
        total_before = len(self.enemies)
        for e in self.enemies:
            if e.death_state < LifecycleState.DEAD:
                self.enemies[i] = e
                i += 1
        del self.enemies[i:]

        removed = total_before - i
        if removed > 0:
            DebugLogger.state(
                f"Removed {removed} inactive enemies",
                category="entity_cleanup"
            )

    # ===========================================================
    # Rendering Pass
    # ===========================================================
    def draw(self):
        """
        Render all active enemies using the global DrawManager.
        """
        for e in self.enemies:
            e.draw(self.draw_manager)
        # No per-frame logging here to avoid console spam

    # ===========================================================
    # Cleanup (External Call)
    # ===========================================================
    def cleanup(self):
        """Immediately remove enemies that are no longer alive."""
        total_before = len(self.enemies)
        i = 0
        for e in self.enemies:
            if e.death_state < LifecycleState.DEAD:
                self.enemies[i] = e
                i += 1
        del self.enemies[i:]

        removed = total_before - i
        if removed > 0:
            DebugLogger.state(
                f"Cleaned up {removed} destroyed enemies",
                category="entity_cleanup"
            )
