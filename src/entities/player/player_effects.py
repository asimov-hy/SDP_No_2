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
from src.core.services.event_manager import get_events, NukeUsedEvent

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
@effect_handler("ADD_HEALTH")
def handle_ADD_HEALTH(player, effect_data):
    """Add health to player (capped at max_health)."""
    amount = effect_data.get("amount", 0)
    old_health = player.health
    player.health = min(player.max_health, player.health + amount)

    DebugLogger.action(
        f"Health +{amount} ({old_health} → {player.health})",
        category="item"
    )

@effect_handler("SPEED_BOOST")
def handle_SPEED_BOOST(player, effect_data):
    """Temporarily multiply player movement speed."""
    multiplier = effect_data.get("multiplier", 1.0)
    duration = effect_data.get("duration", 5.0)
    stack_type = effect_data.get("stack_type", "MULTIPLY")

    player.state_manager.add_stat_modifier("speed", multiplier, duration, stack_type)

    DebugLogger.action(
        f"Speed {multiplier}x for {duration}s",
        category="item"
    )

@effect_handler("MULTIPLY_FIRE_RATE")
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

@effect_handler("USE_NUKE")
def handle_USE_NUKE(player, effect_data):
    """Trigger a screen-clearing nuke."""
    get_events().dispatch(NukeUsedEvent())
    DebugLogger.action("NUKE ACTIVATED! Clearing screen...", category="item")


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
