"""
status_manager.py
-----------------
Generic effect management system for entities_animation.

Responsibilities
----------------
- Track active temporary animation_effects with timers
- Merge interaction states from multiple animation_effects
- Update effect durations each frame
- Provide queries for active animation_effects
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.player.player_state import InteractionState, PlayerEffectState


class StatusManager:
    """Manages temporary status animation_effects on any entity."""

    def __init__(self, entity, config):
        """
        Args:
            entity: Entity instance (Player, Enemy, etc.)
            config: Effect config dict from entity config
        """
        self.entity = entity
        self.effect_config = config
        self.active_effects = {}  # {PlayerEffectState: remaining_time}

    def activate(self, effect: PlayerEffectState) -> bool:
        """
        Activate an effect or refresh its timer if already active.

        Args:
            effect: Effect to activate

        Returns:
            bool: True if activated/refreshed
        """
        if effect == PlayerEffectState.NONE:
            return False

        # Get config for this effect
        effect_name = effect.name.lower()
        if effect_name not in self.effect_config:
            return False

        cfg = self.effect_config[effect_name]
        duration = cfg.get("duration", 0.0)
        self.active_effects[effect] = duration

        # Add or refresh timer
        self.active_effects[effect] = duration

        DebugLogger.action(f"{effect.name}: Duration: {duration:.2f}s")

        # Update entity interaction state
        self._update_entity_state()

        return True

    def update(self, dt: float):
        """
        Update all active effect timers and remove expired ones.

        Args:
            dt: Delta time in seconds
        """
        if not self.active_effects:
            return

        # Decrement timers
        expired = []
        for effect, time_remaining in self.active_effects.items():
            new_time = time_remaining - dt
            if new_time <= 0:
                expired.append(effect)
            else:
                self.active_effects[effect] = new_time

        # Remove expired
        for effect in expired:
            del self.active_effects[effect]
            DebugLogger.state(f"{effect.name} expired")

        # Recalculate state if anything changed
        if expired:
            self._update_entity_state()

    def remove(self, effect: PlayerEffectState):
        """Manually remove an effect."""
        if effect in self.active_effects:
            del self.active_effects[effect]
            self._update_entity_state()

    def is_active(self, effect: PlayerEffectState) -> bool:
        """Check if specific effect is active."""
        return effect in self.active_effects

    def has_any_effect(self) -> bool:
        """Check if any effect is active."""
        return len(self.active_effects) > 0

    def get_active_effects(self) -> list:
        """Get list of currently active animation_effects."""
        return list(self.active_effects.keys())

    def _update_entity_state(self):
        """Recalculate entity interaction state from active animation_effects."""
        old_state = getattr(self.entity, "state", InteractionState.DEFAULT)

        if not self.active_effects:
            if old_state != InteractionState.DEFAULT:
                DebugLogger.state(
                    f"{self.entity.__class__.__name__} interaction mode: "
                    f"{old_state.name} → DEFAULT"
                )
            self.entity.state = InteractionState.DEFAULT
            return

        if not self.active_effects:
            self.entity.state = InteractionState.DEFAULT
            return

        # Find highest interaction state from all active animation_effects
        max_state = InteractionState.DEFAULT

        for effect in self.active_effects.keys():
            effect_name = effect.name.lower()
            cfg = self.effect_config.get(effect_name, {})
            state_str = cfg.get("interaction_state", "DEFAULT")

            # Convert string to enum
            state = getattr(InteractionState, state_str, InteractionState.DEFAULT)

            if state > max_state:
                max_state = state

        if max_state != old_state:
            DebugLogger.state(
                f"{self.entity.__class__.__name__} interaction changed: "
                f"{old_state.name} → {max_state.name}"
            )

        self.entity.state = max_state
