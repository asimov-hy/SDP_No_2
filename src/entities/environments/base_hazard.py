"""
base_hazard.py
--------------
Base class for damage zones (AOE, lasers, environmental hazards).
Hazards go through telegraph → active → fadeout phases.
"""

from src.entities.base_entity import BaseEntity
from src.entities.entity_types import EntityCategory


class HazardState:
    """State machine for hazard lifecycle"""
    TELEGRAPH = 1  # Warning phase
    ACTIVE = 2  # Dealing damage
    FADEOUT = 3  # Ending


class BaseHazard(BaseEntity):
    """
    Base class for environmental hazards and damage zones.

    Examples: laser beams, AOE explosions, spike traps, etc.
    """

    __slots__ = (
        'hazard_state', 'state_timer',
        'telegraph_time', 'active_time', 'fadeout_time'
    )

    def __init__(self, x, y, telegraph_time=0.5, active_time=2.0, **kwargs):
        """
        Initialize hazard with state machine timing.

        Args:
            x, y: Center position
            telegraph_time: Duration of warning phase (seconds)
            active_time: Duration of damage phase (seconds)
            **kwargs: Passed to BaseEntity
        """
        super().__init__(x, y, **kwargs)
        self.category = EntityCategory.HAZARD
        self.collision_tag = "hazard"

        # State machine
        self.hazard_state = HazardState.TELEGRAPH
        self.state_timer = 0.0

        # Timing configuration
        self.telegraph_time = telegraph_time
        self.active_time = active_time
        self.fadeout_time = 0.3  # Default fadeout

    def can_damage(self):
        """Check if hazard is currently dealing damage"""
        return self.hazard_state == HazardState.ACTIVE

    def update(self, dt):
        """
        Base update - advances state machine.
        Subclasses should override and call super().update(dt)
        """
        self.state_timer += dt

        # State machine transitions
        if self.hazard_state == HazardState.TELEGRAPH:
            if self.state_timer >= self.telegraph_time:
                self.hazard_state = HazardState.ACTIVE
                self.state_timer = 0.0

        elif self.hazard_state == HazardState.ACTIVE:
            if self.state_timer >= self.active_time:
                self.hazard_state = HazardState.FADEOUT
                self.state_timer = 0.0

        elif self.hazard_state == HazardState.FADEOUT:
            if self.state_timer >= self.fadeout_time:
                self.mark_dead(immediate=True)