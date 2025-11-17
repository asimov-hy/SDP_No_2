"""
start_scene.py
--------------
Thin orchestrator for start screen.
LOCKED - developers work in start_controller.py instead.
"""

from src.core.runtime.menu_scene import MenuScene
from src.core.debug.debug_logger import DebugLogger
from src.scenes.start.start_controller import StartController


class StartScene(MenuScene):
    """Start screen orchestrator - delegates to StartController."""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        DebugLogger.section("Initializing Scene: StartScene")

        # Create controller
        self.start_ctrl = StartController(self)

        DebugLogger.section("- Finished Initialization", only_title=True)

    def update(self, dt: float):
        """Delegate to controller."""
        self.start_ctrl.update(dt)

    def draw(self, draw_manager):
        """Delegate to controller."""
        self.start_ctrl.draw(draw_manager)

    def handle_event(self, event):
        """Delegate to controller."""
        self.start_ctrl.handle_event(event)

    def reset(self):
        """Reset scene state for pooling."""
        self.start_ctrl.timer = 0.0
        DebugLogger.state("StartScene reset")