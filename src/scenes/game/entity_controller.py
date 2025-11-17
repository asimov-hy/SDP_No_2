"""
entity_controller.py
--------------------
Handles spawn manager, bullet manager, and enemy systems.
Developer B's responsibility.
"""

from src.core.runtime.scene_controller import SceneController


class EntityController(SceneController):
    """Manages entities, spawning, and projectiles."""

    def __init__(self, scene):
        super().__init__(scene)
        self.spawn_manager = scene.spawn_manager
        self.bullet_manager = scene.bullet_manager

    def update(self, dt: float):
        """Update entity spawning, bullets, and cleanup."""
        # 1) Entity updates
        self.spawn_manager.update(dt)

        # 2) Projectiles
        self.bullet_manager.update(dt)

        # 3) Cleanup dead entities
        self.spawn_manager.cleanup()

    def draw(self, draw_manager):
        """Render entities and bullets."""
        self.spawn_manager.draw()
        self.bullet_manager.draw(draw_manager)