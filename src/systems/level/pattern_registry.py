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
            pattern_func (callable): Function(count, width, **kwargs) -> [(x, y), ...]
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
            list[(float, float)]: List of (x, y) positions
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
    Horizontal line formation.

    Args:
        count (int): Number of entities
        game_width (int): Screen width
        game_height (int): Screen height
        config (dict): Contains "edge", "offset_x", "offset_y", "spacing"
    """
    edge = config.get("edge", "top")
    offset_x = config.get("offset_x", 0)
    offset_y = config.get("offset_y", -100)
    spacing = config.get("spacing")

    if spacing is None:
        spacing = game_width // (count + 1)

    positions = []

    if edge in ["top", "bottom"]:
        # Horizontal line
        base_y = offset_y if edge == "top" else game_height + offset_y
        for i in range(count):
            x = spacing * (i + 1) + offset_x
            positions.append((x, base_y))

    elif edge in ["left", "right"]:
        # Vertical line (rotated 90°)
        base_x = offset_x if edge == "left" else game_width + offset_x
        spacing_y = config.get("spacing", game_height // (count + 1))
        for i in range(count):
            y = spacing_y * (i + 1) + offset_y
            positions.append((base_x, y))

    return positions


def pattern_circle(count, game_width, game_height, config, **_):
    """
    Circular formation.

    Args:
        count (int): Number of entities
        game_width (int): Screen width
        game_height (int): Screen height
        config (dict): Contains "radius", "center_x", "center_y"
                       If edge specified, centers on edge position
    """
    import math

    edge = config.get("edge")
    radius = config.get("radius", 200)

    # Determine center based on edge or explicit coords
    if edge:
        offset_x = config.get("offset_x", 0)
        offset_y = config.get("offset_y", -100)

        if edge == "top":
            center_x = game_width // 2 + offset_x
            center_y = offset_y
        elif edge == "bottom":
            center_x = game_width // 2 + offset_x
            center_y = game_height + offset_y
        elif edge == "left":
            center_x = offset_x
            center_y = game_height // 2 + offset_y
        elif edge == "right":
            center_x = game_width + offset_x
            center_y = game_height // 2 + offset_y
        else:
            center_x = game_width / 2
            center_y = -100
    else:
        center_x = config.get("center_x", game_width / 2)
        center_y = config.get("center_y", -100)

    positions = []
    angle_step = (2 * math.pi) / count

    for i in range(count):
        angle = i * angle_step
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        positions.append((x, y))

    return positions


def pattern_v(count, game_width, game_height, config, **_):
    """
    V-formation (chevron).

    Args:
        count (int): Number of entities
        game_width (int): Screen width
        game_height (int): Screen height
        config (dict): Contains "edge", "offset_x", "offset_y",
                       "x_spacing", "y_spacing", "tip_depth"
    """
    edge = config.get("edge", "top")
    offset_x = config.get("offset_x", 0)
    offset_y = config.get("offset_y", -100)
    x_spacing = config.get("x_spacing", 120)
    y_spacing = config.get("y_spacing", 40)
    tip_depth = config.get("tip_depth", 120)

    positions = []

    if edge in ["top", "bottom"]:
        # Horizontal V
        center_x = game_width // 2 + offset_x
        base_y = offset_y if edge == "top" else game_height + offset_y

        for i in range(count):
            rel = i - (count - 1) / 2
            x = center_x + rel * x_spacing
            y = base_y + tip_depth - abs(rel) * y_spacing
            positions.append((x, y))

    elif edge in ["left", "right"]:
        # Vertical V (rotated 90°)
        base_x = offset_x if edge == "left" else game_width + offset_x
        center_y = game_height // 2 + offset_y

        for i in range(count):
            rel = i - (count - 1) / 2
            y = center_y + rel * x_spacing
            x = base_x + tip_depth - abs(rel) * y_spacing
            positions.append((x, y))

    return positions


def pattern_single(count, game_width, game_height, config, **_):
    """
    Single position spawn (or multiple at same position).

    Args:
        count (int): Number of entities
        game_width (int): Screen width
        game_height (int): Screen height
        config (dict): Contains "x", "y" or "edge" with offsets
    """
    # Explicit coordinates
    if "x" in config:
        x = config["x"]
        y = config.get("y", -100)
        return [(x, y)] * count

    # Edge-based
    edge = config.get("edge", "top")
    offset_x = config.get("offset_x", 0)
    offset_y = config.get("offset_y", -100)

    if edge == "top":
        x = game_width / 2 + offset_x
        y = offset_y
    elif edge == "bottom":
        x = game_width / 2 + offset_x
        y = game_height + offset_y
    elif edge == "left":
        x = offset_x
        y = game_height / 2 + offset_y
    elif edge == "right":
        x = game_width + offset_x
        y = game_height / 2 + offset_y
    else:
        x = game_width / 2
        y = -100

    return [(x, y)] * count

def pattern_grid(count, game_width, game_height, config, **_):
    """
    Grid formation.

    Args:
        count (int): Number of entities
        game_width (int): Screen width
        game_height (int): Screen height
        config (dict): Contains "edge", "offset_x", "offset_y",
                       "cols", "row_spacing", "col_spacing"
    """
    import math

    edge = config.get("edge", "top")
    offset_x = config.get("offset_x", 0)
    offset_y = config.get("offset_y", -100)
    cols = config.get("cols")
    row_spacing = config.get("row_spacing", 80)
    col_spacing = config.get("col_spacing", 100)

    if cols is None:
        cols = math.ceil(math.sqrt(count))

    rows = math.ceil(count / cols)

    positions = []

    if edge in ["top", "bottom"]:
        # Horizontal grid
        grid_width = (cols - 1) * col_spacing
        start_x = (game_width - grid_width) / 2 + offset_x
        start_y = offset_y if edge == "top" else game_height + offset_y

        for i in range(count):
            row = i // cols
            col = i % cols
            x = start_x + col * col_spacing
            y = start_y + row * row_spacing
            positions.append((x, y))

    elif edge in ["left", "right"]:
        # Vertical grid (rotated 90°)
        grid_height = (cols - 1) * col_spacing
        start_x = offset_x if edge == "left" else game_width + offset_x
        start_y = (game_height - grid_height) / 2 + offset_y

        for i in range(count):
            row = i // cols
            col = i % cols
            y = start_y + col * col_spacing
            x = start_x + row * row_spacing
            positions.append((x, y))

    return positions


# ===========================================================
# Auto-register all patterns
# ===========================================================
PatternRegistry.register("line", pattern_line)
PatternRegistry.register("v", pattern_v)
PatternRegistry.register("circle", pattern_circle)
PatternRegistry.register("grid", pattern_grid)
PatternRegistry.register("single", pattern_single)