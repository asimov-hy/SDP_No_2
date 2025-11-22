"""
config_manager.py
-----------------
Universal configuration loader for engine and game config.

Features
--------
- Supports .json and .py config files
- Accepts filenames or absolute paths
- Automatically searches multiple config directories
- Recursively merges defaults
- Ignores '_notes' keys for human-readable entities_config
- Logs results through DebugLogger
"""

import os
import json
import importlib.util
from src.core.debug.debug_logger import DebugLogger

# ===========================================================
# Base directories (search order)
# ===========================================================
DATA_ROOT = os.path.join("src", "config")
SEARCH_DIRS = [
    DATA_ROOT,
    os.path.join(DATA_ROOT, "entities"),  # plural fallback
    os.path.join(DATA_ROOT, "levels"),
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
    except (ImportError, AttributeError, FileNotFoundError, SyntaxError) as e:
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
        default_dict (dict, optional): Default fallback config

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

    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        DebugLogger.warn(f"Failed to load {path}: {e} — using defaults", category="loading")
        return default_dict.copy()


# ===========================================================
# Path resolver
# ===========================================================
def _resolve_search_path(filename):
    """Search for a config file across known directories."""
    filename = filename.replace("\\", "/").lstrip("/")

    # Try each search directory
    for directory in SEARCH_DIRS:
        # Allow bare filenames and subpaths
        candidate = os.path.join(directory, filename)
        if os.path.exists(candidate):
            return candidate

        # Try with extensions
        for ext in (".json", ".py"):
            if os.path.exists(candidate + ext):
                return candidate + ext

        # 🔹 NEW: try searching one level deep (e.g., Stage 1.json anywhere under levels_config/)
        for root, _, files in os.walk(directory):
            for file in files:
                if file == filename or file == filename + ".json" or file == filename + ".py":
                    return os.path.join(root, file)

    # Fallback
    return filename

