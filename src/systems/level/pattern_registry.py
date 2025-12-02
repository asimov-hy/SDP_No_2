"""
pattern_registry.py
-------------------
Factory for enemy formation patterns.
Decouples spawn positioning logic from level config.

Performance
-----------
All patterns are pure functions - zero state, zero overhead.
Called only during wave spawn (not per-frame).

Usage
-----
# Register patterns at module load
PatternRegistry.register("line", pattern_line)

# Use in LevelManager
positions = PatternRegistry.get_positions("line", count=5, width=1280)
"""

from src.core.debug.debug_logger import DebugLogger


class PatternRegistry:
    """Static factory for enemy formation patterns."""

    _patterns = {}

    @classmethod
    def register(cls, name, pattern_func):
        """
        Register a pattern function.

        Args:
            name (str): Pattern identifier (used in JSON)
            pattern_func (callable): Function(count, width, **kwargs) -> [(x, y), ...] or [(x, y, metadata), ...]
        """
        cls._patterns[name] = pattern_func
        DebugLogger.system(f"Registered pattern: {name}")

    @classmethod
    def get_positions(cls, pattern_name, count, width, height, config):
        """
        Generate spawn positions for a pattern.

        Args:
            pattern_name (str): Pattern identifier
            count (int): Number of entities to spawn
            width (int): Game width
            height (int): Game height
            config (dict): Pattern configuration with optional edge/offset

        Returns:
            list: List of (x, y) or (x, y, metadata) tuples
        """
        pattern_func = cls._patterns.get(pattern_name)

        if not pattern_func:
            DebugLogger.warn(f"Unknown pattern '{pattern_name}', using fallback")
            return [(width / 2, -100)] * count

        return pattern_func(count, width, height, config)

    @classmethod
    def list_patterns(cls):
        """Get all registered pattern names."""
        return list(cls._patterns.keys())


# ===========================================================
# Built-in Formation Patterns
# ===========================================================

def pattern_line(count, game_width, game_height, config, **_):
    """
    Horizontal or vertical line formation.

    Features:
    - Equal spacing from edge
    - Cross mode: if True, each enemy uses auto-direction (diagonal)
                  if False (default), all enemies move straight

    Args:
        count (int): Number of entities
        game_width (int): Screen width
        game_height (int): Screen height
        config (dict): Contains:
            - "edge": "top", "bottom", "left", "right"
            - "offset": Distance from edge (perpendicular)
            - "spacing": Distance between enemies (parallel to edge)
            - "cross": True/False - enable diagonal auto-direction
    """
    edge = config.get("edge", "top")
    offset = config.get("offset", -100)
    spacing = config.get("spacing")
    cross = config.get("cross", False)

    positions = []

    if edge in ["top", "bottom"]:
        # Horizontal line
        if spacing is None:
            spacing = game_width // (count + 1)

        base_y = offset if edge == "top" else game_height + offset

        for i in range(count):
            x = spacing * (i + 1)
            positions.append((x, base_y, {"use_auto_direction": cross}))

    elif edge in ["left", "right"]:
        # Vertical line
        if spacing is None:
            spacing = game_height // (count + 1)

        base_x = offset if edge == "left" else game_width + offset

        for i in range(count):
            y = spacing * (i + 1)
            positions.append((base_x, y, {"use_auto_direction": cross}))

    return positions


def pattern_v(count, game_width, game_height, config, **_):
    """
    V-formation (chevron).
    Always moves straight (no auto-direction).

    Args:
        count (int): Number of entities
        game_width (int): Screen width
        game_height (int): Screen height
        config (dict): Contains:
            - "edge": "top", "bottom", "left", "right"
            - "offset": Distance from edge (perpendicular)
            - "x_spacing": Horizontal spacing between enemies
            - "y_spacing": Vertical spacing (depth of V)
            - "tip_depth": How far the tip extends
    """
    edge = config.get("edge", "top")
    offset = config.get("offset", -100)
    x_spacing = config.get("x_spacing", 120)
    y_spacing = config.get("y_spacing", 40)
    tip_depth = config.get("tip_depth", 120)

    positions = []

    if edge in ["top", "bottom"]:
        # Horizontal V
        center_x = game_width // 2
        base_y = offset if edge == "top" else game_height + offset

        for i in range(count):
            rel = i - (count - 1) / 2
            x = center_x + rel * x_spacing
            y = base_y + tip_depth - abs(rel) * y_spacing
            positions.append((x, y, {"use_auto_direction": False}))

    elif edge in ["left", "right"]:
        # Vertical V (rotated 90°)
        base_x = offset if edge == "left" else game_width + offset
        center_y = game_height // 2

        for i in range(count):
            rel = i - (count - 1) / 2
            y = center_y + rel * x_spacing
            x = base_x + tip_depth - abs(rel) * y_spacing
            positions.append((x, y, {"use_auto_direction": False}))

    return positions


# ===========================================================
# Auto-register all patterns
# ===========================================================
PatternRegistry.register("line", pattern_line)
PatternRegistry.register("v", pattern_v)