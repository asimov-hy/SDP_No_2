"""
item_types.py
-------------
Defines an enumeration for all item IDs, preventing typos and enabling
static analysis for item-related logic.
"""
from enum import Enum

class ItemType(str, Enum):
    """
    Enumeration of all known item IDs. Inherits from `str` so that members
    can be used directly as string values. This should be kept in sync
with `data/items.json`.
    """
    # --- Power-ups ---
    POWER_UP_SHOTGUN = "power_up_shotgun"
    POWER_UP_LASER = "power_up_laser"

    # --- Health & Lives ---
    HEALTH_KIT_SMALL = "health_kit_small"
    EXTRA_LIFE = "extra_life"

    # --- Score & Utility ---
    SCORE_BONUS_MEDAL = "score_bonus_medal"
    BOMB_ITEM = "bomb_item"

    # --- Non-Collectible / Props ---
    ENEMY_PLANE_WRECKAGE = "enemy_plane_wreckage"

    @classmethod
    def get_all(cls) -> list[str]:
        """
        Returns a list of all defined item type strings.
        """
        return [member.value for member in cls]
