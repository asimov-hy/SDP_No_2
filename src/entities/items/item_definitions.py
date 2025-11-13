"""
item_definitions.py
-------------------------
Defines the single source of truth for item types, their data schemas,
and the system logic to ensure data integrity.
"""
from enum import Enum
from src.core.debug.debug_logger import DebugLogger

# ===========================================================
# 1. Item Type Definitions
# ===========================================================
class ItemType(str, Enum):
    """Enumeration of all known item IDs used in the code."""
    EXTRA_LIFE = "extra_life"
    SCORE_BONUS_MEDAL = "score_bonus_medal"
    DUMMY = "dummy"

# ===========================================================
# 2. Item Schema Definitions
# ===========================================================
EFFECT_SCHEMAS = {
    "ADD_LIVES": {"amount": int},
    "ADD_SCORE": {"amount": int},
}

ITEM_SCHEMA = {
    "name": str,
    "asset_path": str,
    "drop_weight": int,
    "effects": list,
}

# ===========================================================
# 3. system Logic
# ===========================================================
def validate_item_data(all_item_data: dict) -> bool:
    """
    Validates the entire item data from items.json against schemas and enums.
    
    Args:
        all_item_data: The loaded data from items.json.

    Returns:
        True if system passes, False otherwise.
    """
    DebugLogger.system("Starting item data system...", category="system")
    is_valid = True

    # 1. ID Synchronization
    code_ids = {item.value for item in ItemType}
    json_ids = set(all_item_data.keys())

    missing_from_json = code_ids - json_ids
    for item_id in missing_from_json:
        DebugLogger.warn(f"system: Item '{item_id}' is in ItemType but missing from items.json.", category="system")
        is_valid = False

    missing_from_code = json_ids - code_ids
    for item_id in missing_from_code:
        DebugLogger.warn(f"system: Item '{item_id}' is in items.json but missing from ItemType.", category="system")
        is_valid = False

    # 2. Schema and Effect system
    known_effect_types = set(EFFECT_SCHEMAS.keys())
    for item_id, data in all_item_data.items():
        # 2a. Item structure
        for field, expected_type in ITEM_SCHEMA.items():
            if field not in data:
                DebugLogger.warn(f"system: Item '{item_id}' is missing required field '{field}'.", category="system")
                is_valid = False
                continue
            if not isinstance(data[field], expected_type):
                DebugLogger.warn(f"system: Item '{item_id}' field '{field}' should be type '{expected_type.__name__}' but is '{type(data[field]).__name__}'.", category="system")
                is_valid = False

        # 2b. Effects structure
        for effect in data.get("effects", []):
            effect_type = effect.get("type")
            if not effect_type:
                DebugLogger.warn(f"system: Item '{item_id}' has an effect with no 'type' field.", category="system")
                is_valid = False
                continue
            if effect_type not in known_effect_types:
                DebugLogger.warn(f"system: Item '{item_id}' has an unknown effect type: '{effect_type}'.", category="system")
                is_valid = False
                continue
            
            effect_schema = EFFECT_SCHEMAS[effect_type]
            for field, expected_type in effect_schema.items():
                if field not in effect:
                    DebugLogger.warn(f"system: Item '{item_id}' effect '{effect_type}' is missing required field '{field}'.", category="system")
                    is_valid = False
                    continue
                if not isinstance(effect[field], expected_type):
                    DebugLogger.warn(f"system: Item '{item_id}' effect '{effect_type}' field '{field}' should be type '{expected_type.__name__}' but is '{type(effect[field]).__name__}'.", category="system")
                    is_valid = False
    
    return is_valid
