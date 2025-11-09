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

from src.core.game_settings import Debug
from src.core.utils.debug_logger import DebugLogger
from src.systems.combat.collision_hitbox import CollisionHitbox
from src.entities.enemies.enemy_straight import EnemyStraight

# ===========================================================
# Enemy Type Registry
# ===========================================================
ENEMY_TYPES = {
    "straight": EnemyStraight,
    # "zigzag": EnemyZigzag,
    # "shooter": EnemyShooter,
}


class SpawnManager:
    """Central manager responsible for enemy spawning, updates, and rendering."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, draw_manager, display=None):
        """
        Initialize the spawn manager and enemy registry.

        Args:
            draw_manager: Global DrawManager for rendering.
            display (optional): DisplayManager for screen info (future use).
        """
        self.draw_manager = draw_manager
        self.display = display
        self.enemies = []  # Active enemy entities

        # Internal cache used to sync with collision manager
        self._trace_timer = 0.0

        DebugLogger.init("Enemy spawn system initialized")

    # ===========================================================
    # Enemy Spawning
    # ===========================================================
    def spawn_enemy(self, type_name: str, x: float, y: float):
        """
        Spawn a new enemy of the specified type.

        Args:
            type_name (str): Type of enemy ('straight', 'zigzag', etc.).
            x (float): X spawn coordinate.
            y (float): Y spawn coordinate.
        """
        cls = ENEMY_TYPES.get(type_name)
        if not cls:
            DebugLogger.warn(f"Unknown enemy type: '{type_name}'")
            return

        # -------------------------------------------------------
        # Load enemy sprite (fallback to None if not found)
        # -------------------------------------------------------
        image_key = f"enemy_{type_name}"
        try:
            img = self.draw_manager.get_image(image_key)
        except Exception:
            DebugLogger.warn(f"Missing image asset for '{image_key}', using fallback")
            img = None

        # -------------------------------------------------------
        # Instantiate enemy and attach hitbox
        # -------------------------------------------------------
        try:
            enemy = cls(x, y, img)
            enemy.collision_tag = getattr(enemy, "collision_tag", "enemy")

            # Attach scaled hitbox for spatial hashing
            hitbox_scale = getattr(enemy, "hitbox_scale", 1.0)
            enemy.hitbox = CollisionHitbox(enemy, scale=hitbox_scale)
            enemy.has_hitbox = True

            self.enemies.append(enemy)

            DebugLogger.action(
                f"Spawned enemy '{type_name}' at ({x:.0f}, {y:.0f})",
                category="entity_spawning"
            )

        except Exception as e:
            DebugLogger.warn(f"Failed to spawn enemy '{type_name}': {e}")

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
            if not enemy.alive:
                continue
            enemy.update(dt)
            if enemy.has_hitbox:
                enemy.hitbox.update()

        # -------------------------------------------------------
        # Cleanup inactive enemies efficiently
        # -------------------------------------------------------
        before = len(self.enemies)
        self.enemies = [e for e in self.enemies if e.alive]
        removed = before - len(self.enemies)

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
        before = len(self.enemies)
        self.enemies = [e for e in self.enemies if e.alive]
        removed = before - len(self.enemies)

        if removed > 0:
            DebugLogger.state(
                f"Cleaned up {removed} destroyed enemies",
                category="entity_cleanup"
            )
