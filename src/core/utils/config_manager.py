"""
config_manager.py
-----------------
Handles all JSON configuration loading and merging with defaults.
Prevents duplication and keeps entity code clean.
"""

import os
import json
from src.core.utils.debug_logger import DebugLogger

DATA_DIR = os.path.join("src", "data")

def load_json(filename, default_dict):
    """Safely load JSON config, merge with defaults, fallback on error."""
    path = os.path.join(DATA_DIR, filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            DebugLogger.system(f"Loaded {filename}")
            return {**default_dict, **data}
    except Exception as e:
        DebugLogger.warn(f"Failed to load {filename}: {e} — using defaults")
        return default_dict.copy()
