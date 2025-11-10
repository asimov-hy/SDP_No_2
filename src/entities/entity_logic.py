"""
entity_logic.py
---------------
Provides generic runtime logic shared by all game entities.

This module contains standalone functions that operate on entity instances.
Import and call these functions directly on your entity objects.

Responsibilities
----------------
- Manage health, damage application, and death handling.
- Manage interaction states and visual updates.
- Automatically call entity-specific hooks (on_damaged, on_death, etc.)
"""

from src.core.utils.debug_logger import DebugLogger
from src.entities.entity_state import InteractionState


# ===========================================================
# Core Health & Damage Handling
# ===========================================================
def apply_damage(entity, amount: int):
    """
    Apply damage to an entity and handle death if HP reaches zero.

    This function checks for invulnerability, reduces health, calls damage hooks,
    updates visuals, and triggers death handling when appropriate.

    Args:
        entity: The entity taking damage (must have health, collision_tag attributes)
        amount: Amount of damage to apply (integer)

    Hooks Called (if entity has them):
        - entity.on_damaged(amount) - Called after damage is applied
        - entity.on_death() - Called via handle_death() if HP <= 0
    """
    # Check invulnerability via state system
    state = getattr(entity, "state", InteractionState.DEFAULT)
    if isinstance(state, InteractionState) and not state.can_take_damage:
        DebugLogger.state(
            f"{entity.collision_tag} is invulnerable (state={state.name})",
            category="damage"
        )
        return

    # Legacy invulnerability check (for entities not using state system yet)
    if getattr(entity, "is_invulnerable", False):
        DebugLogger.state(
            f"{entity.collision_tag} has is_invulnerable=True",
            category="damage"
        )
        return

    # Reduce health
    entity.health = max(0, entity.health - amount)
    DebugLogger.state(
        f"{entity.collision_tag} took {amount} → HP={entity.health}",
        category="damage"
    )

    # Custom damage reaction (flash, sound, etc.)
    if hasattr(entity, "on_damaged") and callable(entity.on_damaged):
        entity.on_damaged(amount)

    # Update visuals (player/enemy/etc.)
    update_visual_state(entity)

    # Handle death
    if entity.health <= 0:
        handle_death(entity)


# ===========================================================
# Death Handling
# ===========================================================
def handle_death(entity):
    """
    Deactivate an entity when HP reaches zero.

    Marks the entity as dead, disables its hitbox, and calls entity-specific
    death hooks for cleanup, animation, or loot drops.

    Args:
        entity: The entity that died (must have alive, collision_tag attributes)

    Hooks Called (if entity has them):
        - entity.on_death() - Called for entity-specific death behavior
    """
    if not getattr(entity, "alive", True):
        return  # Already dead

    entity.alive = False

    # Disable hitbox to prevent further collisions
    if hasattr(entity, "hitbox") and entity.hitbox:
        entity.hitbox.active = False

    DebugLogger.state(
        f"{entity.collision_tag} destroyed.",
        category="state"
    )

    # Entity-specific cleanup
    if hasattr(entity, "on_death") and callable(entity.on_death):
        entity.on_death()

    # Optional: visual removal effect
    update_visual_state(entity)


# ===========================================================
# Interaction State Management
# ===========================================================
def set_interaction_state(entity, state: InteractionState | int):
    """
    Set entity's current interaction state and update hitbox collision rules.

    Changes how the entity interacts with damage and collision systems.
    Updates hitbox flags based on the new state level.

    Args:
        entity: The entity to modify (must have state, hitbox attributes)
        state: New interaction state (InteractionState enum or int)

    State Effects on Hitbox:
        - DEFAULT (0): All collisions active
        - INVINCIBLE (1): All collisions active (damage ignored elsewhere)
        - INTANGIBLE (2): Selective collision (no enemy collision)
        - CLIP_THROUGH (3): All collisions disabled

    Hooks Called (if entity has them):
        - entity.on_state_change(state) - Called after state change
    """
    # Convert int to enum if needed
    if isinstance(state, int):
        try:
            state = InteractionState(state)
        except ValueError:
            DebugLogger.warn(f"Unknown interaction value: {state}")
            state = InteractionState.DEFAULT

    entity.state = state

    # Update hitbox collision rules based on state
    if hasattr(entity, "hitbox") and entity.hitbox:
        # CLIP_THROUGH (3): disable all collision
        entity.hitbox.active = state < InteractionState.CLIP_THROUGH
        entity.hitbox.collides_with_environment = state < InteractionState.CLIP_THROUGH
        # INTANGIBLE (2): disable enemy collision
        entity.hitbox.collides_with_enemies = state < InteractionState.INTANGIBLE

    DebugLogger.state(
        f"[StateChange] {entity.collision_tag} → {state.name} ({state.value})",
        category="state"
    )

    # Optional per-entity state response
    if hasattr(entity, "on_state_change") and callable(entity.on_state_change):
        entity.on_state_change(state)


# ===========================================================
# Universal Visual Update Logic
# ===========================================================
def update_visual_state(entity):
    """
    Update an entity's appearance after damage, death, or other events.

    Delegates to entity-specific update_visual_state() method if available,
    otherwise applies a generic health-based color tint for debugging.

    Args:
        entity: The entity to update visually

    Entity Methods Called (if available):
        - entity.update_visual_state() - Custom visual update logic

    Fallback Behavior:
        If no custom update_visual_state() method exists, applies a red tint
        based on current HP ratio (for debugging/prototyping).
    """
    # Check if entity has its own visual update method
    if hasattr(entity, "update_visual_state") and callable(entity.update_visual_state):
        # Get the actual function object
        entity_method = entity.update_visual_state

        # Check if it's not this same function (avoid recursion)
        # This happens if someone does: entity.update_visual_state = update_visual_state
        if hasattr(entity_method, "__func__"):
            if entity_method.__func__ is update_visual_state:
                # It's the same function, skip to fallback
                pass
            else:
                # It's a different method, call it
                entity.update_visual_state()
                return
        else:
            # It's a method, call it
            entity.update_visual_state()
            return

    # Generic fallback: tint based on HP ratio (for debugging)
    health = getattr(entity, "health", 1)
    max_health = getattr(entity, "max_health", 1)

    if max_health > 0:
        ratio = health / max_health
        color = (255, int(255 * ratio), int(255 * ratio))

        if hasattr(entity, "color"):
            entity.color = color
            DebugLogger.state(
                f"{entity.collision_tag} color={color}",
                category="effects"
            )