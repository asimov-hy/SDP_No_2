"""
animation_data.py
-----------------
Centralized animation data loading and caching.
Entities never touch this directly - AnimationManager handles lookup.
"""

import os
import pygame
from src.core.debug.debug_logger import DebugLogger
from src.core.services.config_manager import load_config

_DATA = None
_FRAME_CACHE = {}  # {(path, scale): Surface}


def _load_data():
    """Load animation config once via config_manager."""
    global _DATA
    if _DATA is None:
        _DATA = load_config("animations.json", default_dict={})
    return _DATA


def _load_frame(path, scale=1.0):
    """Load and cache a single frame."""
    cache_key = (path, scale)
    if cache_key in _FRAME_CACHE:
        return _FRAME_CACHE[cache_key]

    if not os.path.exists(path):
        DebugLogger.warn(f"Animation frame not found: {path}")
        return None

    try:
        img = pygame.image.load(path).convert_alpha()
        if scale != 1.0:
            new_size = (int(img.get_width() * scale), int(img.get_height() * scale))
            img = pygame.transform.scale(img, new_size)
        _FRAME_CACHE[cache_key] = img
        return img
    except Exception as e:
        DebugLogger.warn(f"Failed to load frame {path}: {e}")
        return None


def get_animation_config(category: str, entity_name: str, anim_type: str) -> dict:
    """
    Get animation config for an entity.

    Args:
        category: "enemy", "player", etc.
        entity_name: "straight", "homing", etc.
        anim_type: "death", "damage", etc.

    Returns:
        Config dict with 'frames', 'duration', 'scale', etc.
    """
    data = _load_data()

    # Lookup path: animations.json -> category -> anim_type -> entity_name
    category_data = data.get(category, {})
    anim_data = category_data.get(anim_type, {})

    # Try specific entity, then "default"
    config = anim_data.get(entity_name, anim_data.get("default", {}))
    return config


def get_animation_frames(category: str, entity_name: str, anim_type: str) -> list:
    """Get loaded frame surfaces for an animation."""
    config = get_animation_config(category, entity_name, anim_type)

    frame_paths = config.get("frames", [])
    scale = config.get("scale", 1.0)

    frames = []
    for path in frame_paths:
        frame = _load_frame(path, scale)
        if frame:
            frames.append(frame)

    return frames


def get_animation_duration(category: str, entity_name: str, anim_type: str) -> float:
    """Get animation duration."""
    config = get_animation_config(category, entity_name, anim_type)
    return config.get("duration", 0.5)