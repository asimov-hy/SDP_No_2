"""
player_effects.py
-----------------
Item effects handlers for the player.

Responsibilities
----------------
- Apply item effects to player stats and state
- Handle temporary and permanent modifications
- Dispatch effects from items.json
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState

EFFECT_HANDLERS = {}


def effect_handler(effect_name: str):
    """Decorator to auto-register effects handlers."""
    def decorator(func):
        EFFECT_HANDLERS[effect_name] = func
        return func
    return decorator


# ===========================================================
# effects Handlers
# ===========================================================
def handle_ADD_HEALTH(player, effect_data):
    """Add health to player (capped at max_health)."""
    amount = effect_data.get("amount", 0)
    old_health = player.health
    player.health = min(player.max_health, player.health + amount)

    DebugLogger.action(
        f"Health +{amount} ({old_health} → {player.health})",
        category="item"
    )


def handle_ADD_MAX_HEALTH(player, effect_data):
    """Increase max health and heal for the difference."""
    amount = effect_data.get("amount", 0)
    old_max = player.max_health
    player.max_health += amount
    player.health += amount

    DebugLogger.action(
        f"Max Health +{amount} ({old_max} → {player.max_health})",
        category="item"
    )


def handle_FULL_HEAL(player, effect_data):
    """Restore player to full health."""
    old_health = player.health
    player.health = player.max_health

    DebugLogger.action(
        f"Full heal ({old_health} → {player.health})",
        category="item"
    )


def handle_MULTIPLY_SPEED(player, effect_data):
    """Temporarily multiply player movement speed."""
    multiplier = effect_data.get("multiplier", 1.0)
    duration = effect_data.get("duration", 5.0)
    stack_type = effect_data.get("stack_type", "MULTIPLY")

    player.state_manager.add_stat_modifier("speed", multiplier, duration, stack_type)

    DebugLogger.action(
        f"Speed {multiplier}x for {duration}s",
        category="item"
    )


def handle_MULTIPLY_FIRE_RATE(player, effect_data):
    """Temporarily multiply player fire rate."""
    multiplier = effect_data.get("multiplier", 1.0)
    duration = effect_data.get("duration", 5.0)
    stack_type = effect_data.get("stack_type", "MULTIPLY")

    player.state_manager.add_stat_modifier("fire_rate", multiplier, duration, stack_type)

    DebugLogger.action(
        f"Fire rate {multiplier}x for {duration}s",
        category="item"
    )


def handle_ADD_DAMAGE(player, effect_data):
    """Add flat damage bonus to player projectiles."""
    amount = effect_data.get("amount", 1)
    duration = effect_data.get("duration", 5.0)
    stack_type = effect_data.get("stack_type", "ADD")

    player.state_manager.add_stat_modifier("damage", amount, duration, stack_type)

    DebugLogger.action(
        f"Damage +{amount} for {duration}s",
        category="item"
    )


def handle_GRANT_SHIELD(player, effect_data):
    """Grant temporary shield/invincibility."""
    duration = effect_data.get("duration", 3.0)

    from src.entities.player.player_state import PlayerEffectState
    player.state_manager.timed_state(PlayerEffectState.IFRAME)

    DebugLogger.action(
        f"Shield granted for {duration}s",
        category="item"
    )


def handle_ADD_SCORE(player, effect_data):
    """Add score points (debug only - no score system implemented)."""
    amount = effect_data.get("amount", 0)

    DebugLogger.action(
        f"Score +{amount} (not implemented - debug only)",
        category="item"
    )


# ===========================================================
# effects Dispatcher
# ===========================================================
def apply_item_effects(player, effects: list):
    """
    Apply item effects to player.

    Args:
        player: Player entity
        effects: List of effects dicts from items.json
    """
    if player.death_state != LifecycleState.ALIVE:
        return

    for effect in effects:
        effect_type = effect.get("type")

        handler = EFFECT_HANDLERS.get(effect_type)
        if handler:
            handler(player, effect)
        else:
            DebugLogger.warn(f"Unknown effects type: {effect_type}", category="item")
