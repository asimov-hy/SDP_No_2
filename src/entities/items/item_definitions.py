"""
item_definitions.py
-------------------------
Defines the single source of truth for item types, their data schemas,
and the validation logic to ensure data integrity.

Example of a complete item definition in items.json:

"score_bonus_medal": {
  "name": "Bonus Medal",
  "asset_path": "assets/images/items/dummy_item.png",
  "drop_weight": 100,
  "physics": {
    "velo_x": 0,
    "velo_y": 80,
    "hitbox_scale": 0.85
  },
  "effects": [
    {
      "type": "ADD_SCORE",
      "amount": 500
    }
  ]
}
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
# 3. Validation Logic
# ===========================================================
def validate_item_data(all_item_data: dict) -> bool:
    """
    Validates the entire item data from items.json against schemas and enums.
    
    Args:
        all_item_data: The loaded data from items.json.

    Returns:
        True if validation passes, False otherwise.
    """
    DebugLogger.system("Starting item data validation...", category="validation")
    is_valid = True

    # 1. ID Synchronization
    code_ids = {item.value for item in ItemType}
    json_ids = set(all_item_data.keys())

    missing_from_json = code_ids - json_ids
    for item_id in missing_from_json:
        DebugLogger.warn(f"Validation: Item '{item_id}' is in ItemType but missing from items.json.", category="validation")
        is_valid = False

    missing_from_code = json_ids - code_ids
    for item_id in missing_from_code:
        DebugLogger.warn(f"Validation: Item '{item_id}' is in items.json but missing from ItemType.", category="validation")
        is_valid = False

    # 2. Schema and Effect Validation
    known_effect_types = set(EFFECT_SCHEMAS.keys())
    for item_id, data in all_item_data.items():
        # 2a. Item structure (required fields)
        for field, expected_type in ITEM_SCHEMA.items():
            if field not in data:
                DebugLogger.warn(f"Validation: Item '{item_id}' is missing required field '{field}'.", category="validation")
                is_valid = False
                continue
            if not isinstance(data[field], expected_type):
                DebugLogger.warn(f"Validation: Item '{item_id}' field '{field}' should be type '{expected_type.__name__}' but is '{type(data[field]).__name__}'.", category="validation")
                is_valid = False

        # 2b. Optional 'physics' object validation
        if "physics" in data:
            if not isinstance(data["physics"], dict):
                DebugLogger.warn(f"Validation: 'physics' field in item '{item_id}' must be an object.", category="validation")
                is_valid = False
            else:
                physics_data = data["physics"]
                optional_fields = {
                    "velo_x": (int, float),
                    "velo_y": (int, float),
                    "hitbox_scale": (int, float)
                }
                for field, expected_types in optional_fields.items():
                    if field in physics_data and not isinstance(physics_data[field], expected_types):
                        DebugLogger.warn(f"Validation: Optional field 'physics.{field}' in item '{item_id}' has incorrect type. Expected number.", category="validation")
                        is_valid = False

        # 2c. Effects structure
        for effect in data.get("effects", []):
            effect_type = effect.get("type")
            if not effect_type:
                DebugLogger.warn(f"Validation: Item '{item_id}' has an effect with no 'type' field.", category="validation")
                is_valid = False
                continue
            if effect_type not in known_effect_types:
                DebugLogger.warn(f"Validation: Item '{item_id}' has an unknown effect type: '{effect_type}'.", category="validation")
                is_valid = False
                continue
            
            effect_schema = EFFECT_SCHEMAS[effect_type]
            for field, expected_type in effect_schema.items():
                if field not in effect:
                    DebugLogger.warn(f"Validation: Item '{item_id}' effect '{effect_type}' is missing required field '{field}'.", category="validation")
                    is_valid = False
                    continue
                if not isinstance(effect[field], expected_type):
                    DebugLogger.warn(f"Validation: Item '{item_id}' effect '{effect_type}' field '{field}' should be type '{expected_type.__name__}' but is '{type(effect[field]).__name__}'.", category="validation")
                    is_valid = False
    
    if is_valid:
        DebugLogger.system("Item data validation successful.", category="validation")
    else:
        DebugLogger.fail("Item data validation failed with one or more warnings.", category="validation")

    return is_valid
