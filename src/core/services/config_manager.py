"""
config_manager.py
-----------------
Universal configuration loader for engine and game data.

Features
--------
- Supports .json and .py config files
- Accepts filenames or absolute paths
- Automatically searches multiple data directories
- Recursively merges defaults
- Ignores '_notes' keys for human-readable configs
- Logs results through DebugLogger
"""

import os
import json
import importlib.util
from src.core.debug.debug_logger import DebugLogger

# ===========================================================
# Base directories (search order)
# ===========================================================
DATA_ROOT = os.path.join("src", "data")
SEARCH_DIRS = [
    os.path.join(DATA_ROOT, "config"),
    os.path.join(DATA_ROOT, "configs"),  # plural fallback
    os.path.join(DATA_ROOT, "levels"),
    DATA_ROOT,  # final fallback
]


# ===========================================================
# Internal helpers
# ===========================================================
def _merge_dicts(default, override):
    """Recursively merge two dictionaries while ignoring '_notes'."""
    merged = default.copy()
    for key, value in override.items():
        if key == "_notes":
            continue
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_py_module(py_path):
    """Load a Python config file and return DEFAULT_CONFIG if present."""
    try:
        spec = importlib.util.spec_from_file_location("config_module", py_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        DebugLogger.system(f"Loaded {os.path.basename(py_path)} (Python)", category="loading")
        return getattr(module, "DEFAULT_CONFIG", {})
    except Exception as e:
        DebugLogger.warn(f"Failed to load Python config {py_path}: {e}", category="loading")
        return {}


# ===========================================================
# Main loader
# ===========================================================
def load_config(filename, default_dict=None):
    """
    Universal configuration loader.

    Args:
        filename (str): Filename or full path (.json or .py)
        default_dict (dict, optional): Default fallback data

    Returns:
        dict: Merged configuration
    """
    if default_dict is None:
        default_dict = {}

    # 1. Detect if an absolute or relative path was provided
    if os.path.exists(filename):
        path = filename
    else:
        path = _resolve_search_path(filename)

    # 2. Append extension if missing
    if not os.path.splitext(path)[1]:
        for ext in (".json", ".py"):
            if os.path.exists(path + ext):
                path += ext
                break

    # 3. Load the configuration
    try:
        if path.endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            DebugLogger.system(f"Loaded {os.path.basename(path)}", category="loading")

        elif path.endswith(".py"):
            data = _load_py_module(path)
        else:
            raise FileNotFoundError(f"Unsupported config type: {path}")

        return _merge_dicts(default_dict, data)

    except Exception as e:
        DebugLogger.warn(f"Failed to load {path}: {e} — using defaults", category="loading")
        return default_dict.copy()


# ===========================================================
# Path resolver
# ===========================================================
def _resolve_search_path(filename):
    """Search for a config file across known directories."""
    # Normalize slashes and remove redundant leading paths
    filename = filename.replace("\\", "/").lstrip("/")
    # Try each search directory
    for directory in SEARCH_DIRS:
        candidate = os.path.join(directory, filename)
        if os.path.exists(candidate):
            return candidate
        # Try with extensions
        for ext in (".json", ".py"):
            if os.path.exists(candidate + ext):
                return candidate + ext

    # Fallback to filename as-is (will trigger error log)
    return filename
