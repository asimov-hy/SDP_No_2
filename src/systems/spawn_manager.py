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

from src.core.settings import DebugConfig
from src.core.utils.debug_logger import DebugLogger
from src.entities.enemies.enemy_basic import EnemyBasic


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

        DebugLogger.init("SpawnManager", "Initialized enemy spawn system")

    # ===========================================================
    # Enemy Spawning
    # ===========================================================
    def spawn_enemy(self, type_name: str, x: float, y: float):
        """
        Spawn a new enemy of the specified type.

        Args:
            type_name (str): Type of enemy ('basic').
            x (float): X spawn coordinate.
            y (float): Y spawn coordinate.
        """
        try:
            if type_name == "basic":
                img = self.draw_manager.get_image("enemy_basic")
                enemy = EnemyBasic(x, y, img)
            else:
                DebugLogger.warn("SpawnManager", f"Unknown enemy type: '{type_name}'")
                return

            self.enemies.append(enemy)
            if DebugConfig.VERBOSE_ENTITY_INIT:
                DebugLogger.action("SpawnManager", f"Spawned '{type_name}' enemy at ({x}, {y})")


        except Exception as e:
            DebugLogger.warn("SpawnManager", f"Failed to spawn enemy '{type_name}': {e}")

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

        removed_count = 0
        for e in list(self.enemies):  # Safe iteration for removal
            e.update(dt)
            if not e.alive:
                self.enemies.remove(e)
                removed_count += 1

        if removed_count > 0:
            DebugLogger.state("SpawnManager", f"Removed {removed_count} inactive enemies")

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
