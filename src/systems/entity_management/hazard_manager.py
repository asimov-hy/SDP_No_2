"""
hazard_manager.py
-----------------
Manages temporary damage zones (mines, lasers, impact zones).
"""

from src.entities.entity_state import LifecycleState
from src.core.debug.debug_logger import DebugLogger


class HazardManager:
    """Spawns and manages boss/environmental hazards."""

    def __init__(self, draw_manager, collision_manager=None):
        self.draw_manager = draw_manager
        self.collision_manager = collision_manager
        self.hazards = []
        self._alive_cache = []
        self._cache_dirty = True

    def spawn(self, hazard_class, x, y, **kwargs):
        """
        Spawn a hazard instance.

        Args:
            hazard_class: The hazard class to instantiate
            x, y: Spawn position
            **kwargs: Passed to hazard constructor

        Returns:
            Hazard instance
        """
        kwargs.setdefault("draw_manager", self.draw_manager)
        hazard = hazard_class(x, y, **kwargs)
        self.hazards.append(hazard)
        self._cache_dirty = True

        if self.collision_manager:
            self.collision_manager.register_hitbox(hazard)

        DebugLogger.system(
            f"Spawned {hazard_class.__name__} at ({x:.0f}, {y:.0f})",
            category="hazard"
        )
        return hazard

    def update(self, dt):
        """Update all active hazards."""
        if self._cache_dirty:
            self._alive_cache = [h for h in self.hazards if h.death_state < LifecycleState.DEAD]
            self._cache_dirty = False

        for hazard in self._alive_cache:
            hazard.update(dt)

    def draw(self):
        """Draw all active hazards."""
        for hazard in self._alive_cache:
            hazard.draw(self.draw_manager)

    def cleanup(self):
        """Remove dead hazards."""
        removed = 0
        for hazard in self.hazards:
            if hazard.death_state >= LifecycleState.DEAD:
                if self.collision_manager:
                    self.collision_manager.unregister_hitbox(hazard)
                removed += 1

        if removed > 0:
            self.hazards = [h for h in self.hazards if h.death_state < LifecycleState.DEAD]
            self._cache_dirty = True

    def clear_all(self):
        """Clear all hazards (boss death, phase transition)."""
        for hazard in self.hazards:
            if self.collision_manager:
                self.collision_manager.unregister_hitbox(hazard)
        self.hazards.clear()
        self._alive_cache.clear()
        self._cache_dirty = False

    def count(self):
        """Return active hazard count."""
        return len(self._alive_cache)