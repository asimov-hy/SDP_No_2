"""
gameplay_controller.py
----------------------
Handles player logic, collision detection, and physics systems.
Developer A's responsibility.
"""

from src.core.runtime.scene_controller import SceneController
from src.core.debug.debug_logger import DebugLogger


class GameplayController(SceneController):
    """Coordinates player and collision - NO game logic."""

    def __init__(self, scene):
        super().__init__(scene)
        self.player = scene.player
        self.collision_manager = scene.collision_manager

    def update(self, dt: float):
        """Just call existing systems in order."""
        self.player.update(dt)  # Player already handles input internally
        self.collision_manager.update()
        self.collision_manager.detect()

    def draw(self, draw_manager):
        """Just render existing systems."""
        from src.core.runtime.game_settings import Debug
        self.player.draw(draw_manager)
        if Debug.HITBOX_VISIBLE:
            self.collision_manager.draw_debug(draw_manager)