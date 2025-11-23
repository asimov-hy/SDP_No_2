"""
instant_transition.py
---------------------
Instant transition (no animation) - current behavior.
"""

from src.scenes.transitions.i_transition import ITransition


class InstantTransition(ITransition):
    """No-op transition that completes immediately."""

    def __init__(self):
        super().__init__(duration=0.0)
        self.complete = True  # Always complete

    def update(self, dt: float) -> bool:
        """Instant transitions complete immediately."""
        return True

    def draw(self, draw_manager, old_scene, new_scene):
        """Just draw the new scene (no effect)."""
        if new_scene:
            new_scene.draw(draw_manager)
