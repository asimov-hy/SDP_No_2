"""
config_manager.py
-----------------
Universal configuration loader for engine and game config.

Features:
- Supports .json and .py config files
- Builds file index once at startup for O(1) lookups
- Recursively merges defaults
- Ignores '_notes' keys for human-readable configs
"""

import os
import json
import importlib.util
from src.core.debug.debug_logger import DebugLogger


# ===========================================================
# Configuration
# ===========================================================

DATA_ROOT = os.path.join("src", "config")

SEARCH_DIRS = [
    ".",
    DATA_ROOT,
    os.path.join(DATA_ROOT, "entities"),
    os.path.join(DATA_ROOT, "missions"),
    os.path.join(DATA_ROOT, "animations"),
]

_FILE_INDEX = None


# ===========================================================
# Public API
# ===========================================================

def load_config(filename, default_dict=None, strict=False):
    """
    Load a configuration file.

    Args:
        filename: Filename or full path (.json or .py)
        default_dict: Default fallback config
        strict: If True, raise exception on missing file

    Returns:
        dict: Merged configuration
    """
    if default_dict is None:
        default_dict = {}

    # Resolve path (absolute paths pass through, others use index)
    if os.path.isabs(filename) and os.path.exists(filename):
        path = filename
    else:
        path = _resolve_search_path(filename)

    # Load and merge
    try:
        if path.endswith(".py"):
            data = _load_py_module(path)
        else:
            data = _load_json(path)

        return _merge_dicts(default_dict, data)

    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        if strict:
            raise FileNotFoundError(f"Config not found: {filename}") from e
        DebugLogger.warn(f"Failed to load {path}: {e} - using defaults", category="loading")
        return default_dict.copy()


def build_file_index():
    """Scan config directories and cache all file paths. Call once at startup."""
    global _FILE_INDEX
    _FILE_INDEX = {}

    for directory in SEARCH_DIRS:
        if not os.path.isdir(directory):
            continue
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith((".json", ".py")):
                    if file not in _FILE_INDEX:
                        _FILE_INDEX[file] = os.path.join(root, file)

    DebugLogger.init(f"Config index: {len(_FILE_INDEX)} files", category="loading")


def rebuild_file_index():
    """Clear and rebuild index. Use during development hot-reload."""
    global _FILE_INDEX
    _FILE_INDEX = None
    build_file_index()


def get_indexed_files():
    """Return copy of file index for debugging."""
    if _FILE_INDEX is None:
        build_file_index()
    return _FILE_INDEX.copy()


# ===========================================================
# Path Resolution
# ===========================================================

def _resolve_search_path(filename):
    """O(1) lookup from pre-built index."""
    if _FILE_INDEX is None:
        build_file_index()

    filename = filename.replace("\\", "/").lstrip("/")

    # Direct match
    if filename in _FILE_INDEX:
        return _FILE_INDEX[filename]

    # Try with extensions
    for ext in (".json", ".py"):
        key = filename + ext
        if key in _FILE_INDEX:
            return _FILE_INDEX[key]

    # Fallback for absolute paths or missing files
    return filename


# ===========================================================
# File Loaders
# ===========================================================

def _load_json(path):
    """Load JSON config file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    DebugLogger.system(f"Loaded {os.path.basename(path)}", category="loading")
    return data


def _load_py_module(path):
    """Load Python config file and return DEFAULT_CONFIG if present."""
    try:
        spec = importlib.util.spec_from_file_location("config_module", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        DebugLogger.system(f"Loaded {os.path.basename(path)} (Python)", category="loading")
        return getattr(module, "DEFAULT_CONFIG", {})
    except (ImportError, AttributeError, SyntaxError) as e:
        DebugLogger.warn(f"Failed to load Python config {path}: {e}", category="loading")
        return {}


# ===========================================================
# Merge Utilities
# ===========================================================

def _merge_dicts(default, override):
    """Recursively merge two dicts. Ignores '_notes' keys."""
    merged = default.copy()
    for key, value in override.items():
        if key == "_notes":
            continue
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged