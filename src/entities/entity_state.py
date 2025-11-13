"""
entity_state.py
---------------
Defines universal constants and enumerations for all entity types.
"""

from enum import IntEnum


class EntityCategory:
    """
    High-level logical grouping for entities.
    Used for both runtime categorization AND registry registration.

    Example:
        class EnemyNew(BaseEnemy):
            __registry_category__ = EntityCategory.ENEMY
            __registry_name__ = "new"
    """
    PLAYER = "player"
    ENEMY = "enemy"
    PROJECTILE = "projectile"  # Used for bullets (both player and enemy)
    ENVIRONMENT = "environment"
    PICKUP = "pickup"
    EFFECT = "effect"

    # Valid categories for EntityRegistry registration
    # (PLAYER excluded - not spawnable via registry)
    REGISTRY_VALID = {ENEMY, PROJECTILE, PICKUP, ENVIRONMENT, EFFECT}


# ===========================================================
# Collision Tag Constants
# ===========================================================
class CollisionTags:
    """
    Standard collision tags for entity.collision_tag.
    Prevents typos and enables IDE autocomplete.
    """
    NEUTRAL = "neutral"

    PLAYER = "player"
    PLAYER_BULLET = "player_bullet"

    ENEMY = "enemy"
    ENEMY_BULLET = "enemy_bullet"

    PICKUP = "pickup"
    HAZARD = "hazard"

class LifecycleState(IntEnum):
    """
    Tracks the life/death progression of an entity.
    Used for death animation control and cleanup timing.
    """
    ALIVE = 0
    DYING = 1      # Playing death animation/effect
    DEAD = 2       # Ready for cleanup
