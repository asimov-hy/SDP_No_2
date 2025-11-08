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

from src.core.settings import Debug
from src.core.utils.debug_logger import DebugLogger

from src.systems.hitbox import Hitbox

from src.entities.enemies.enemy_straight import EnemyStraight
# Future: from src.entities.enemies.enemy_zigzag import EnemyZigzag
# Future: from src.entities.enemies.enemy_shooter import EnemyShooter

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

        # Timer used to limit log spam for trace-level outputs
        self._trace_timer = 0.0

        DebugLogger.init("Initialized enemy spawn system")

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
        try:
            # -------------------------------------------------------
            # Resolve enemy class dynamically from registry
            # -------------------------------------------------------
            cls = ENEMY_TYPES.get(type_name)
            if not cls:
                DebugLogger.warn(f"Unknown enemy type: '{type_name}'")
                return

            # -------------------------------------------------------
            # Auto-load matching image asset (enemy_straight, etc.)
            # -------------------------------------------------------
            image_key = f"enemy_{type_name}"
            try:
                img = self.draw_manager.get_image(image_key)
            except Exception:
                DebugLogger.warn(f"Missing image asset for '{image_key}', using fallback.")
                img = None

            # -------------------------------------------------------
            # Instantiate enemy and register hitbox
            # -------------------------------------------------------
            enemy = cls(x, y, img)
            enemy.hitbox = Hitbox(enemy, scale=getattr(enemy, "hitbox_scale", 1.0))
            self.enemies.append(enemy)

            if Debug.VERBOSE_ENTITY_INIT:
                DebugLogger.action(f"Spawned '{type_name}' enemy at ({x}, {y})")

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

        # Update all enemies
        for enemy in self.enemies:
            enemy.update(dt)

        # Remove dead enemies efficiently
        initial_count = len(self.enemies)
        self.enemies = [e for e in self.enemies if e.alive]
        removed_count = initial_count - len(self.enemies)

        if removed_count > 0 and Debug.VERBOSE_ENTITY_DEATH:
            DebugLogger.state(f"Removed {removed_count} inactive enemies")

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
