"""Entity types."""


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
    PICKUP = "pickup"
    OBSTACLE = "obstacle"
    HAZARD = "hazard"
    ENVIRONMENT = "environment"
    PARTICLE = "particle"

    # Valid categories for EntityRegistry registration
    # (PLAYER excluded - not spawnable via registry)
    REGISTRY_VALID = frozenset({ENEMY, PROJECTILE, PICKUP, OBSTACLE, HAZARD, ENVIRONMENT, PARTICLE})


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
    ENVIRONMENT = "environment"
