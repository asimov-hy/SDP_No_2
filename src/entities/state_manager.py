"""
state_manager.py
----------------
Generic status effect and stat modifier system for entities.

Responsibilities
----------------
- Track active temporary effects with timers
- Manage stat modifiers (speed boost, damage boost, etc.)
- Merge interaction states from multiple active effects
- Provide queries for active effects
"""

from enum import IntEnum
from typing import Dict, List, Optional, Any

from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import InteractionState


# Constants
PERMANENT_DURATION = -1


# Stat Modifier System
class StackType:
    """How modifiers combine with base stats."""
    ADD = "ADD"
    MULTIPLY = "MULTIPLY"


class StatModifier:
    """
    Manages temporary stat modifiers for an entity.

    Supports both additive and multiplicative modifiers with independent timers.
    Formula: (base_value + additive_sum) * multiplicative_product
    """

    __slots__ = ('_modifiers',)

    def __init__(self):
        self._modifiers: Dict[str, List[dict]] = {}

    def add(self, stat: str, value: float, duration: float, stack_type: str = StackType.MULTIPLY):
        """
        Add a stat modifier.

        Args:
            stat: Stat name ("speed", "fire_rate", "damage")
            value: Modifier value
            duration: Duration in seconds (PERMANENT_DURATION for permanent)
            stack_type: StackType.ADD or StackType.MULTIPLY
        """
        if stat not in self._modifiers:
            self._modifiers[stat] = []

        self._modifiers[stat].append({
            "value": value,
            "time": duration,
            "stack": stack_type
        })

        DebugLogger.action(f"Stat modifier: {stat} {stack_type} {value} for {duration}s")

    def update(self, dt: float):
        """Decrement timers and remove expired modifiers."""
        empty_stats = []

        for stat, mods in self._modifiers.items():
            # Filter in-place: keep non-expired
            for mod in mods:
                if mod["time"] != PERMANENT_DURATION:
                    mod["time"] -= dt
            self._modifiers[stat] = [m for m in mods if m["time"] == PERMANENT_DURATION or m["time"] > 0]

            if not mods:
                empty_stats.append(stat)

        # Clean up empty stat lists
        for stat in empty_stats:
            del self._modifiers[stat]

    def calculate(self, stat_name: str, base_value: float) -> float:
        """
        Calculate final stat value with all active modifiers.

        Args:
            stat_name: Name of stat
            base_value: Base value before modifiers

        Returns:
            Modified value: (base + additive_sum) * multiplicative_product
        """
        if stat_name not in self._modifiers:
            return base_value

        additive = 0.0
        multiplicative = 1.0

        for mod in self._modifiers[stat_name]:
            if mod["stack"] == StackType.ADD:
                additive += mod["value"]
            else:
                multiplicative *= mod["value"]

        return (base_value + additive) * multiplicative

    def remove_all(self, stat_name: str):
        """Remove all modifiers for a specific stat."""
        self._modifiers.pop(stat_name, None)

    def has_modifier(self, stat_name: str) -> bool:
        """Check if stat has any active modifiers."""
        return bool(self._modifiers.get(stat_name))

    def clear(self):
        """Remove all modifiers."""
        self._modifiers.clear()


# ===================================================================
# State Manager
# ===================================================================

class StateManager:
    """
    Manages temporary status effects on any entity.

    Works with any IntEnum effect type (PlayerEffectState, EnemyEffectState, etc.)
    """

    __slots__ = ('entity', 'state_config', '_active_states', '_cached_interaction', 'stat_modifiers')

    def __init__(self, entity, config: dict):
        """
        Args:
            entity: Entity instance (Player, Enemy, etc.)
            config: Effects config dict from entity JSON
        """
        self.entity = entity
        self.state_config = config
        self._active_states: Dict[IntEnum, dict] = {}  # {effect: {"time": float, "interaction": InteractionState}}
        self._cached_interaction = InteractionState.DEFAULT
        self.stat_modifiers = StatModifier()

    # ===================================================================
    # Effect Activation
    # ===================================================================

    def timed_state(self, effect: IntEnum, duration: float = None, apply_debuffs: bool = True) -> bool:
        """
        Activate a timed effect.

        Args:
            effect: Effect enum value (e.g., PlayerEffectState.STUN)
            duration: Override config duration (optional)
            apply_debuffs: Whether to apply configured debuffs

        Returns:
            True if activated, False if effect not configured
        """
        if effect.value == 0:  # NONE equivalent
            return False

        effect_name = effect.name.lower()
        cfg = self.state_config.get(effect_name)
        if cfg is None:
            return False

        cfg_duration = cfg.get("duration", 0.0)
        final_duration = duration if duration is not None else cfg_duration
        interaction = self._parse_interaction_state(cfg.get("interaction_state", "DEFAULT"))

        self._active_states[effect] = {
            "time": final_duration,
            "interaction": interaction,
            "config": cfg  # Store for chaining and queries
        }

        # Apply debuffs if configured
        if apply_debuffs:
            debuffs = cfg.get("debuffs", {})
            for stat, stat_cfg in debuffs.items():
                self.add_stat_modifier(
                    stat,
                    stat_cfg.get("multiplier", 1.0),
                    stat_cfg.get("duration", final_duration)
                )

        DebugLogger.action(f"{effect.name}: Duration {final_duration:.2f}s")
        self._recalculate_interaction()
        return True

    def set_state(self, effect: IntEnum) -> bool:
        """
        Activate a permanent effect.

        Args:
            effect: Effect enum value

        Returns:
            True if activated, False if effect not configured
        """
        if effect.value == 0:
            return False

        effect_name = effect.name.lower()
        cfg = self.state_config.get(effect_name)
        if cfg is None:
            return False

        interaction = self._parse_interaction_state(cfg.get("interaction_state", "DEFAULT"))

        self._active_states[effect] = {
            "time": PERMANENT_DURATION,
            "interaction": interaction
        }

        DebugLogger.action(f"{effect.name}: Permanent")
        self._recalculate_interaction()
        return True

    def clear_state(self, effect: IntEnum):
        """Remove a specific effect."""
        if effect in self._active_states:
            del self._active_states[effect]
            self._recalculate_interaction()

    def clear_all(self):
        """Remove all active effects."""
        self._active_states.clear()
        self.stat_modifiers.clear()
        self._recalculate_interaction()

    # ===================================================================
    # Stat Modifiers (Delegated)
    # ===================================================================

    def add_stat_modifier(self, stat: str, value: float, duration: float, stack_type: str = StackType.MULTIPLY):
        """Add a stat modifier."""
        self.stat_modifiers.add(stat, value, duration, stack_type)

    def get_stat(self, stat_name: str, base_value: float) -> float:
        """Get modified stat value."""
        return self.stat_modifiers.calculate(stat_name, base_value)

    def extend_state(self, effect: IntEnum, additional_time: float) -> bool:
        """Extend duration of an active state."""
        if effect not in self._active_states:
            return False

        data = self._active_states[effect]
        if data["time"] == PERMANENT_DURATION:
            return False

        data["time"] += additional_time
        DebugLogger.action(f"{effect.name}: Extended by {additional_time:.2f}s")
        return True

    def get_state_config(self, effect: IntEnum) -> dict:
        """Get config for active state."""
        data = self._active_states.get(effect)
        return data.get("config", {}) if data else {}

    # ===================================================================
    # Update Loop
    # ===================================================================

    def update(self, dt: float):
        """
        Update all active effects and stat modifiers.

        Args:
            dt: Delta time in seconds
        """
        self.stat_modifiers.update(dt)

        if not self._active_states:
            return

        expired = []

        for effect, data in self._active_states.items():
            if data["time"] == PERMANENT_DURATION:
                continue

            data["time"] -= dt
            if data["time"] <= 0:
                expired.append(effect)

        for effect in expired:
            cfg = self._active_states[effect].get("config", {})
            del self._active_states[effect]
            DebugLogger.state(f"{effect.name} expired")

            # Handle state chaining
            next_state_name = cfg.get("next_state")
            if next_state_name:
                self._trigger_next_state(effect, next_state_name)

        if expired:
            self._recalculate_interaction()

    # ===================================================================
    # Queries
    # ===================================================================

    def has_state(self, effect: IntEnum) -> bool:
        """Check if specific effect is active."""
        return effect in self._active_states

    def has_any_effect(self) -> bool:
        """Check if any effect is active."""
        return bool(self._active_states)

    def get_active_effects(self) -> tuple:
        """Get tuple of currently active effects."""
        return tuple(self._active_states.keys())

    def get_remaining_time(self, effect: IntEnum) -> float:
        """
        Get remaining time for an effect.

        Returns:
            Remaining seconds, PERMANENT_DURATION if permanent, 0.0 if not active
        """
        data = self._active_states.get(effect)
        return data["time"] if data else 0.0

    # ===================================================================
    # Internal
    # ===================================================================

    def _parse_interaction_state(self, state_str: str) -> InteractionState:
        """Convert string to InteractionState enum."""
        try:
            return InteractionState[state_str]
        except (KeyError, AttributeError):
            DebugLogger.warn(f"Invalid interaction_state: {state_str}")
            return InteractionState.DEFAULT

    def _recalculate_interaction(self):
        """Recalculate entity interaction state from active effects."""
        old_state = getattr(self.entity, "state", InteractionState.DEFAULT)

        if not self._active_states:
            if old_state != InteractionState.DEFAULT:
                DebugLogger.state(
                    f"{self.entity.__class__.__name__} interaction: "
                    f"{old_state.name} -> DEFAULT"
                )
            self.entity.state = InteractionState.DEFAULT
            self._cached_interaction = InteractionState.DEFAULT
            return

        # Find highest interaction state (cached on activation)
        max_state = InteractionState.DEFAULT
        for data in self._active_states.values():
            if data["interaction"] > max_state:
                max_state = data["interaction"]

        if max_state != old_state:
            DebugLogger.state(
                f"{self.entity.__class__.__name__} interaction: "
                f"{old_state.name} -> {max_state.name}"
            )

        self.entity.state = max_state
        self._cached_interaction = max_state

    def _trigger_next_state(self, current_effect: IntEnum, state_name: str):
        """Trigger next state in chain by name."""
        # Use same enum class as current effect
        effect_class = type(current_effect)
        try:
            next_effect = effect_class[state_name.upper()]
            self.timed_state(next_effect)
            DebugLogger.state(f"State chain: {current_effect.name} → {next_effect.name}")

        except KeyError:
            DebugLogger.warn(f"Unknown next_state: {state_name}")
