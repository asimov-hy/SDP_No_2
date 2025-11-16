"""
level_controller.py
-------------------
Handles level loading, progression, and transitions.
Developer C's responsibility.
"""

from src.core.runtime.scene_controller import SceneController
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState
from src.systems.level.level_registry import LevelRegistry


class LevelController(SceneController):
    """Manages level progression and stage transitions."""

    def __init__(self, scene):
        super().__init__(scene)
        self.level_manager = scene.level_manager
        self.campaign = scene.campaign
        self.current_level_idx = scene.current_level_idx

        # Bind level complete callback
        self.level_manager.on_stage_complete = self._on_stage_complete

    def update(self, dt: float):
        """Update level timers and wave progression."""
        self.level_manager.update(dt)

    def on_enter(self):
        """Load the first level when scene starts."""
        start_level = LevelRegistry.get_default_start()
        if start_level:
            DebugLogger.state(f"Starting level: {start_level.name}")
            self.level_manager.load(start_level.path)
        else:
            DebugLogger.warn("No start level found")

    def _on_stage_complete(self):
        """Callback fired by LevelManager when stage ends."""
        if self.scene.player.death_state != LifecycleState.ALIVE:
            DebugLogger.system("Player dead - skipping level progression")
            return

        if self.current_level_idx < len(self.campaign):
            current_level = self.campaign[self.current_level_idx]
            DebugLogger.system(f"Level complete: {current_level.name}")
        else:
            DebugLogger.system(f"Level {self.current_level_idx + 1} complete")

        self.scene.spawn_manager.reset()
        self.current_level_idx += 1

        if self.current_level_idx < len(self.campaign):
            next_level = self.campaign[self.current_level_idx]

            # Auto-unlock next level
            LevelRegistry.unlock(next_level.id)

            DebugLogger.state(f"Loading: {next_level.name} ({next_level.path})")
            self.level_manager.load(next_level.path)
        else:
            DebugLogger.system("Campaign complete")