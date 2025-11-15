"""
player_effects.py
-----------------
Handles item effects and stat modifications for the player.

Responsibilities
----------------
- StatModifier: Manages temporary stat multipliers
- Effect handlers: Apply item effects to player
- Effect dispatcher: Routes effects to appropriate handlers
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import DeathState


class StatModifier:
    """Manages temporary stat modifiers with stacking and duration."""

    def __init__(self):
        self.modifiers = {}  # {stat_name: [modifier_dict, ...]}

    def add(self, stat: str, value: float, duration: float, stack_type: str):
        """
        Add a stat modifier.

        Args:
            stat: Stat name (e.g., "speed", "fire_rate")
            value: Multiplier value
            duration: Duration in seconds (-1 for permanent)
            stack_type: "ADD" or "REPLACE"
        """
        if stat not in self.modifiers:
            self.modifiers[stat] = []

        # REPLACE: clear existing modifiers for this stat
        if stack_type == "REPLACE":
            self.modifiers[stat].clear()

        # Add new modifier
        modifier = {
            "value": value,
            "duration": duration,
            "stack_type": stack_type
        }
        self.modifiers[stat].append(modifier)

        DebugLogger.action(f"Stat modifier added: {stat} x{value} for {duration}s ({stack_type})")

    def update(self, dt: float):
        """
        Update all modifier durations and remove expired ones.

        Args:
            dt: Delta time in seconds
        """
        for stat_name in list(self.modifiers.keys()):
            expired = []

            for i, modifier in enumerate(self.modifiers[stat_name]):
                if modifier["duration"] < 0:  # Permanent
                    continue

                modifier["duration"] -= dt
                if modifier["duration"] <= 0:
                    expired.append(i)

            # Remove expired (reverse order to maintain indices)
            for i in reversed(expired):
                self.modifiers[stat_name].pop(i)
                DebugLogger.state(f"Stat modifier expired: {stat_name}")

            # Remove stat entry if no modifiers left
            if not self.modifiers[stat_name]:
                del self.modifiers[stat_name]

    def calculate(self, stat_name: str, base_value: float) -> float:
        """
        Calculate final stat value with all active modifiers.

        Args:
            stat_name: Name of the stat
            base_value: Base value before modifiers

        Returns:
            Modified value
        """
        if stat_name not in self.modifiers:
            return base_value

        # Multiply all active modifiers
        result = base_value
        for modifier in self.modifiers[stat_name]:
            result *= modifier["value"]

        return result

    def remove_all(self, stat_name: str):
        """
        Remove all modifiers for a stat.

        Args:
            stat_name: Name of the stat
        """
        if stat_name in self.modifiers:
            del self.modifiers[stat_name]

    def has_modifier(self, stat_name: str) -> bool:
        """
        Check if a stat has active modifiers.

        Args:
            stat_name: Name of the stat

        Returns:
            True if stat has active modifiers
        """
        return stat_name in self.modifiers and len(self.modifiers[stat_name]) > 0

    # ===========================================================
    # Effect Handler Functions
    # ===========================================================

    def handle_ADD_HEALTH(player, effect_data):
        """Add health without exceeding max health."""
        amount = effect_data["amount"]
        player.health = min(player.max_health, player.health + amount)
        DebugLogger.action(f"Health +{amount} (now {player.health}/{player.max_health})")

    def handle_ADD_MAX_HEALTH(player, effect_data):
        """Increase max health and heal by the same amount."""
        amount = effect_data["amount"]
        player.max_health += amount
        player.health += amount
        DebugLogger.action(f"Max health +{amount} (now {player.health}/{player.max_health})")

    def handle_FULL_HEAL(player, effect_data):
        """Restore health to maximum."""
        player.health = player.max_health
        DebugLogger.action(f"Full heal (now {player.health}/{player.max_health})")

    def handle_MULTIPLY_SPEED(player, effect_data):
        """Apply speed multiplier."""
        multiplier = effect_data["multiplier"]
        duration = effect_data.get("duration", -1)
        stack_type = effect_data.get("stack_type", "ADD")

        player.status_manager.add_stat_modifier(
            "speed", multiplier, duration, stack_type
        )

    def handle_MULTIPLY_FIRE_RATE(player, effect_data):
        """Apply fire rate multiplier."""
        multiplier = effect_data["multiplier"]
        duration = effect_data.get("duration", -1)
        stack_type = effect_data.get("stack_type", "ADD")

        player.status_manager.add_stat_modifier(
            "fire_rate", multiplier, duration, stack_type
        )

    def handle_ADD_DAMAGE(player, effect_data):
        """Apply damage modifier (additive)."""
        amount = effect_data["amount"]
        duration = effect_data.get("duration", -1)
        stack_type = effect_data.get("stack_type", "ADD")

        player.status_manager.add_stat_modifier(
            "damage", amount, duration, stack_type
        )

    def handle_GRANT_SHIELD(player, effect_data):
        """Grant temporary invincibility shield."""
        from src.entities.player.player_state import PlayerEffectState

        duration = effect_data["duration"]
        player.status_manager.set_timed_status(
            PlayerEffectState.INVINCIBLE,
            duration
        )

    # ===========================================================
    # Effect Dispatcher
    # ===========================================================

    def apply_item_effects(player, effects):
        """
        Apply all effects from an item to the player.

        Args:
            player: Player instance
            effects: List of effect dicts from items.json
        """

        # Don't apply effects if player is dead
        if player.death_state != DeathState.ALIVE:
            return

        for effect in effects:
            effect_type = effect["type"]

            # Route to appropriate handler
            if effect_type == "ADD_HEALTH":
                handle_ADD_HEALTH(player, effect)
            elif effect_type == "ADD_MAX_HEALTH":
                handle_ADD_MAX_HEALTH(player, effect)
            elif effect_type == "FULL_HEAL":
                handle_FULL_HEAL(player, effect)
            elif effect_type == "MULTIPLY_SPEED":
                handle_MULTIPLY_SPEED(player, effect)
            elif effect_type == "MULTIPLY_FIRE_RATE":
                handle_MULTIPLY_FIRE_RATE(player, effect)
            elif effect_type == "ADD_DAMAGE":
                handle_ADD_DAMAGE(player, effect)
            elif effect_type == "GRANT_SHIELD":
                handle_GRANT_SHIELD(player, effect)
            else:
                DebugLogger.warn(f"Unknown effect type: {effect_type}")