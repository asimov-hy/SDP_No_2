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
from src.core.services.event_manager import get_events
from src.systems.effects.nuke_pulse import NukePulse


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
def _validate_effect(effect_data: dict, required: list, effect_name: str) -> bool:
    """Validate effect_data has required keys with correct types."""
    for key, expected_type in required:
        val = effect_data.get(key)
        if val is None:
            DebugLogger.warn(f"{effect_name}: missing '{key}'", category="item")
            return False
        if not isinstance(val, expected_type):
            DebugLogger.warn(f"{effect_name}: '{key}' should be {expected_type.__name__}", category="item")
            return False
    return True

@effect_handler("ADD_HEALTH")
def handle_ADD_HEALTH(player, effect_data):
    """Add health to player (capped at max_health)."""
    if not _validate_effect(effect_data, [("amount", (int, float))], "ADD_HEALTH"):
        return

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
    if not _validate_effect(effect_data, [("multiplier", (int, float)), ("duration", (int, float))], "SPEED_BOOST"):
        return

    multiplier = effect_data.get("multiplier", 1.0)
    duration = effect_data.get("duration", 5.0)
    stack_type = effect_data.get("stack_type", "MULTIPLY")

    player.state_manager.add_stat_modifier("speed", multiplier, duration, stack_type)

    # Start buff particle emitter
    particle_preset = effect_data.get("particle_preset")
    if particle_preset:
        player.add_buff_emitter("speed", particle_preset)

    DebugLogger.action(
        f"Speed {multiplier}x for {duration}s",
        category="item"
    )

@effect_handler("MULTIPLY_FIRE_RATE")
def handle_MULTIPLY_FIRE_RATE(player, effect_data):
    """Temporarily multiply player fire rate."""
    if not _validate_effect(effect_data, [("multiplier", (int, float)), ("duration", (int, float))], "MULTIPLY_FIRE_RATE"):
        return

    multiplier = effect_data.get("multiplier", 1.0)
    duration = effect_data.get("duration", 5.0)
    stack_type = effect_data.get("stack_type", "MULTIPLY")

    player.state_manager.add_stat_modifier("fire_rate", multiplier, duration, stack_type)

    # Start buff particle emitter
    particle_preset = effect_data.get("particle_preset")
    if particle_preset:
        player.add_buff_emitter("fire_rate", particle_preset)

    DebugLogger.action(
        f"Fire rate {multiplier}x for {duration}s",
        category="item"
    )


@effect_handler("USE_NUKE")
def handle_USE_NUKE(player, effect_data):
    """Trigger nuke with expanding pulse effect."""
    # Get effects_manager from spawn_manager's scene reference
    effects_manager = player._spawn_manager._effects_manager

    pulse = NukePulse(
        center=player.rect.center,
        start_speed=effect_data.get("start_speed", 1600),
        end_speed=effect_data.get("end_speed", 200),
        damage=effect_data.get("damage", 9999),
        color=tuple(effect_data.get("color", [255, 255, 150])),
    )
    effects_manager.spawn(pulse)

    DebugLogger.action("NUKE ACTIVATED! Pulse expanding...", category="item")


@effect_handler("SPAWN_SHIELD")
def handle_SPAWN_SHIELD(player, effect_data):
    """Spawn or extend item shield duration."""
    if not _validate_effect(effect_data, [("duration", (int, float))], "SPAWN_SHIELD"):
        return

    duration = effect_data.get("duration", 5.0)
    radius = effect_data.get("radius", 56)
    knockback = effect_data.get("knockback", 150)
    damage = effect_data.get("damage", 1)
    color = tuple(effect_data.get("color", [100, 255, 150]))

    # Check if item shield already active
    if player._item_shield is not None:
        # Extend by half duration
        player.extend_item_shield(duration * 0.5)
        DebugLogger.action(f"Shield extended by {duration * 0.5}s", category="item")
    else:
        # Spawn new shield
        player.spawn_item_shield(
            duration=duration,
            radius=radius,
            knockback=knockback,
            damage=damage,
            color=color
        )
        DebugLogger.action(f"Item shield spawned for {duration}s", category="item")


# ===========================================================
# effects Dispatcher
# ===========================================================
def apply_item_effects(player, effects: list, particle_preset: str = None):
    """
    Apply item effects to player.

    Args:
        player: Player entity
        effects: List of effects dicts from items.json
        particle_preset: Particle preset name for duration effects
    """
    if player.death_state != LifecycleState.ALIVE:
        return

    for effect in effects:
        effect_type = effect.get("type")

        # Inject particle_preset for duration-based effects
        if particle_preset and effect.get("duration"):
            effect = {**effect, "particle_preset": particle_preset}

        handler = EFFECT_HANDLERS.get(effect_type)
        if handler:
            handler(player, effect)
        else:
            DebugLogger.warn(f"Unknown effects type: {effect_type}", category="item")
