"""
effects_manager.py
------------------
Manages screen-wide visual effects independent of entity system.
Supports cutscene control - effects can run while gameplay is paused.
"""

from src.core.debug.debug_logger import DebugLogger


class EffectsManager:
    """Centralized manager for visual effects."""

    def __init__(self, spawn_manager):
        """
        Args:
            spawn_manager: Reference to get active entities for effects that need them
        """
        self.spawn_manager = spawn_manager
        self.active_effects = []
        self.paused = False

        DebugLogger.init_entry("EffectsManager")

    def spawn(self, effect):
        """
        Add an effect to be managed.

        Args:
            effect: Object with update(dt, entities), draw(draw_manager), active property
        """
        self.active_effects.append(effect)
        DebugLogger.action(f"Spawned effect: {type(effect).__name__}", category="effects")

    def update(self, dt):
        """Update all active effects."""
        if self.paused or not self.active_effects:
            return

        entities = self.spawn_manager.entities if self.spawn_manager else []

        for effect in self.active_effects:
            if effect.active:
                effect.update(dt, entities)

        # Cleanup finished effects
        before = len(self.active_effects)
        self.active_effects = [e for e in self.active_effects if e.active]
        removed = before - len(self.active_effects)

        if removed > 0:
            DebugLogger.state(f"Cleaned up {removed} effects", category="effects")

    def draw(self, draw_manager):
        """Draw all active effects."""
        for effect in self.active_effects:
            if effect.active:
                effect.draw(draw_manager)

    def pause(self):
        """Pause effect updates (for menus)."""
        self.paused = True

    def resume(self):
        """Resume effect updates."""
        self.paused = False

    def clear(self):
        """Remove all effects."""
        self.active_effects.clear()
        DebugLogger.state("Cleared all effects", category="effects")