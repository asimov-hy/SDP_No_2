"""
state_manager.py
-----------------
Generic effects management system for entities_animation.

Responsibilities
----------------
- Track active temporary animation_effects with timers
- Merge interaction states from multiple animation_effects
- Update effects durations each frame
- Provide queries for active animation_effects
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import InteractionState
from src.entities.player.player_state import PlayerEffectState


# ===========================================================
# Stat Modifier System
# ===========================================================
class StatModifier:
    """Manages temporary stat modifiers for an entity."""

    def __init__(self):
        """Initialize empty modifier storage."""
        # {stat_name: [(value, remaining_time, stack_type), ...]}
        self.modifiers = {}

    def add(self, stat: str, value: float, duration: float, stack_type: str = "MULTIPLY"):
        """
        Add a stat modifier.

        Args:
            stat: Stat name ("speed", "fire_rate", "damage")
            value: Modifier value (multiplier or additive)
            duration: Duration in seconds (-1 = permanent)
            stack_type: "MULTIPLY" or "ADD"
        """
        if stat not in self.modifiers:
            self.modifiers[stat] = []

        self.modifiers[stat].append({
            "value": value,
            "time": duration,
            "stack": stack_type
        })

        DebugLogger.action(
            f"Stat modifier: {stat} {stack_type} {value}x for {duration}s"
        )

    def update(self, dt: float):
        """Decrement timers and remove expired modifiers."""
        for stat in list(self.modifiers.keys()):
            expired = []

            for i, mod in enumerate(self.modifiers[stat]):
                if mod["time"] == -1:
                    continue  # Permanent

                mod["time"] -= dt
                if mod["time"] <= 0:
                    expired.append(i)

            # Remove expired (reverse order to preserve indices)
            for i in reversed(expired):
                self.modifiers[stat].pop(i)

            # Clean up empty stat lists
            if not self.modifiers[stat]:
                del self.modifiers[stat]

    def calculate(self, stat_name: str, base_value: float) -> float:
        """
        Calculate final stat value with all active modifiers.

        Args:
            stat_name: Name of stat
            base_value: Base value before modifiers

        Returns:
            Modified value
        """
        if stat_name not in self.modifiers:
            return base_value

        # Apply all modifiers
        additive = 0.0
        multiplicative = 1.0

        for mod in self.modifiers[stat_name]:
            if mod["stack"] == "ADD":
                additive += mod["value"]
            else:  # MULTIPLY
                multiplicative *= mod["value"]

        return (base_value + additive) * multiplicative

    def remove_all(self, stat_name: str):
        """Remove all modifiers for a specific stat."""
        if stat_name in self.modifiers:
            del self.modifiers[stat_name]

    def has_modifier(self, stat_name: str) -> bool:
        """Check if stat has any active modifiers."""
        return stat_name in self.modifiers and len(self.modifiers[stat_name]) > 0


class StateManager:
    """Manages temporary status animation_effects on any entity."""

    def __init__(self, entity, config):
        """
        Args:
            entity: Entity instance (Player, Enemy, etc.)
            config: effects config dict from entity config
        """
        self.entity = entity
        self.state_config = config
        self.active_states = {}  # {PlayerEffectState: remaining_time}

        self.stat_modifiers = StatModifier()

    def timed_state(self, effect: PlayerEffectState) -> bool:
        if effect == PlayerEffectState.NONE:
            return False

        # Get config for this effects
        effect_name = effect.name.lower()
        if effect_name not in self.state_config:
            return False

        cfg = self.state_config[effect_name]
        duration = cfg.get("duration", 0.0)

        # Add or refresh timer
        self.active_states[effect] = duration

        DebugLogger.action(f"{effect.name}: Duration: {duration:.2f}s")

        # Update entity interaction state
        self._update_entity_state()

        return True

    def set_state(self, effect: PlayerEffectState) -> bool:
        """
        Activate a permanent state (duration = -1).

        Args:
            effect: State to activate permanently

        Returns:
            bool: True if activated
        """
        if effect == PlayerEffectState.NONE:
            return False

        # Get config for this effects
        effect_name = effect.name.lower()
        if effect_name not in self.state_config:
            return False

        # Set permanent state (duration = -1)
        self.active_states[effect] = -1

        DebugLogger.action(f"{effect.name}: Permanent state")

        # Update entity interaction state
        self._update_entity_state()

        return True

    def add_stat_modifier(self, stat: str, value: float, duration: float, stack_type: str):
        """
        Add a stat modifier.

        Args:
            stat: Stat name (e.g., "speed", "fire_rate")
            value: Multiplier value
            duration: Duration in seconds (-1 for permanent)
            stack_type: "ADD" or "REPLACE"
        """
        self.stat_modifiers.add(stat, value, duration, stack_type)

    def get_stat(self, stat_name: str, base_value: float) -> float:
        """
        Get modified stat value.

        Args:
            stat_name: Name of stat
            base_value: Base value before modifiers

        Returns:
            Modified value
        """
        return self.stat_modifiers.calculate(stat_name, base_value)

    def update(self, dt: float):
        """
        Update all active effects timers and remove expired ones.

        Args:
            dt: Delta time in seconds
        """
        # Update stat modifiers
        self.stat_modifiers.update(dt)

        # Update timed states
        expired = []
        for effect, time_remaining in self.active_states.items():
            if time_remaining == -1:
                continue  # Permanent state, don't decrement
            new_time = time_remaining - dt
            if new_time <= 0:
                expired.append(effect)
            else:
                self.active_states[effect] = new_time

        # Remove expired
        for effect in expired:
            del self.active_states[effect]
            DebugLogger.state(f"{effect.name} expired")

        # Recalculate state if anything changed
        if expired:
            self._update_entity_state()

    def clear_state(self, effect: PlayerEffectState):
        """Manually remove an effects."""
        if effect in self.active_states:
            del self.active_states[effect]
            self._update_entity_state()

    def has_state(self, effect: PlayerEffectState) -> bool:
        """Check if specific effects is active."""
        return effect in self.active_states

    def has_any_effect(self) -> bool:
        """Check if any effects is active."""
        return len(self.active_states) > 0

    def get_active_effects(self) -> list:
        """Get list of currently active animation_effects."""
        return list(self.active_states.keys())

    def _update_entity_state(self):
        """Recalculate entity interaction state from active animation_effects."""
        old_state = getattr(self.entity, "state", InteractionState.DEFAULT)

        if not self.active_states:

            if old_state != InteractionState.DEFAULT:
                DebugLogger.state(
                    f"{self.entity.__class__.__name__} interaction mode: "
                    f"{old_state.name} → DEFAULT"
                )

            self.entity.state = InteractionState.DEFAULT
            return

        # Find highest interaction state from all active animation_effects
        max_state = InteractionState.DEFAULT

        for effect in self.active_states.keys():
            effect_name = effect.name.lower()
            cfg = self.state_config.get(effect_name, {})
            state_str = cfg.get("interaction_state", "DEFAULT")

            # Convert string to enum
            try:
                state = InteractionState[state_str]
            except (KeyError, AttributeError):
                DebugLogger.warn(f"Invalid interaction_state: {state_str}")
                state = InteractionState.DEFAULT

            if state > max_state:
                max_state = state

        if max_state != old_state:
            DebugLogger.state(
                f"{self.entity.__class__.__name__} interaction changed: "
                f"{old_state.name} → {max_state.name}"
            )

        self.entity.state = max_state
