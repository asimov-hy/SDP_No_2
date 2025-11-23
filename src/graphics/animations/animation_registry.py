"""
animation_registry.py
---------------------
Automatic animation registration system.
Zero runtime overhead - all registration happens at import time.

Performance:
- O(1) dict lookup for animation functions
- No runtime registration cost
- Minimal error handling in hot path
"""

import inspect

# Global registry: {entity_tag: {anim_name: function}}
registry = {}


def register(entity_tag: str, anim_name: str = None):
    """
    Decorator to auto-register animation functions.

    Registration happens once at module import time (zero runtime cost).

    Args:
        entity_tag: Entity collision tag (e.g., "player", "enemy_straight")
        anim_name: Animation name (e.g., "damage", "death").
                   If None, uses function name.

    Usage:
        @register("player", "damage")
        def damage_player(entity, t):
            blink(entity, t)

        @register("player")  # Uses function name "death"
        def death(entity, t):
            fade_out(entity, t)

    Returns:
        Decorated function (unchanged, just registered)
    """

    def decorator(func):
        from src.core.debug.debug_logger import DebugLogger

        sig = inspect.signature(func)
        if len(sig.parameters) < 2:
            DebugLogger.warn(
                f"Invalid signature for {func.__name__}: "
                f"needs (entity, t) parameters, got {list(sig.parameters.keys())}"
            )
            return func  # Return unregistered to prevent crashes

        # Use provided name or function name
        name = anim_name or func.__name__

        # Build nested dict structure
        if entity_tag not in registry:
            registry[entity_tag] = {}

        if name in registry[entity_tag]:
            DebugLogger.warn(
                f"Overwriting animation '{entity_tag}.{name}'"
            )

        registry[entity_tag][name] = func

        # Log successful registration
        DebugLogger.state(
            f"Registered animation [{entity_tag}.{name}] -> {func.__name__}",
            category="loading"
        )

        return func

    return decorator


def get_animation(entity_tag: str, anim_name: str):
    """
    Fast O(1) lookup for animation function.

    Args:
        entity_tag: Entity's collision tag
        anim_name: Animation type to retrieve

    Returns:
        Animation function or None if not found
        (AnimationManager handles None gracefully)

    Performance:
        - Two dict.get() calls with defaults (no KeyError)
        - No validation or type checking in hot path
        - O(1) → O(1) lookup complexity
    """
    return registry.get(entity_tag, {}).get(anim_name)


def get_animations_for_entity(entity_tag: str):
    """
    Get all registered animations for an entity tag.

    Useful for debugging and validation.

    Args:
        entity_tag: Entity's collision tag

    Returns:
        Dict of {anim_name: function} or empty dict
    """
    return registry.get(entity_tag, {})
