"""
entity_state.py
---------------
Defines universal constants and enumerations for all entity types.
"""


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
