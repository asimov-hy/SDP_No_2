"""
pattern_registry.py
-------------------
Factory for enemy formation patterns.
Decouples spawn positioning logic from level data.

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
    def get_positions(cls, pattern_name, count, width, **kwargs):
        """
        Generate spawn positions for a pattern.

        Args:
            pattern_name (str): Pattern identifier
            count (int): Number of enemies to spawn
            width (int): Screen width for calculations
            **kwargs: Pattern-specific parameters

        Returns:
            list[(float, float)]: List of (x, y) positions
        """
        pattern_func = cls._patterns.get(pattern_name)

        if not pattern_func:
            DebugLogger.warn(f"Unknown pattern '{pattern_name}', using fallback")
            return [(width / 2, -100)]  # Center fallback

        return pattern_func(count, width, **kwargs)

    @classmethod
    def list_patterns(cls):
        """Get all registered pattern names."""
        return list(cls._patterns.keys())


# ===========================================================
# Built-in Formation Patterns
# ===========================================================

def pattern_line(count, width, y_offset=-100, spacing=None, **_):
    """
    Horizontal line formation.

    Args:
        count (int): Number of enemies
        width (int): Screen width
        y_offset (float): Spawn Y position
        spacing (float): Optional fixed spacing between enemies
    """
    if spacing is None:
        spacing = width // (count + 1)

    return [(spacing * (i + 1), y_offset) for i in range(count)]


def pattern_v(count, width, y_offset=-100, x_spacing=120, y_spacing=40, tip_depth=120, **_):
    """
    V-formation (chevron).

    Args:
        count (int): Number of enemies
        width (int): Screen width
        y_offset (float): Base Y position
        x_spacing (float): Horizontal spacing between enemies
        y_spacing (float): Vertical offset per enemy from center
        tip_depth (float): How far forward the tip extends
    """
    center_x = width // 2
    positions = []

    for i in range(count):
        rel = i - (count - 1) / 2  # Distance from center (-2, -1, 0, 1, 2)
        x = center_x + rel * x_spacing
        y = y_offset + tip_depth - abs(rel) * y_spacing
        positions.append((x, y))

    return positions


def pattern_circle(count, width, radius=200, center_x=None, center_y=-100, **_):
    """
    Circular formation.

    Args:
        count (int): Number of enemies
        width (int): Screen width
        radius (float): Circle radius
        center_x (float): Circle center X (defaults to screen center)
        center_y (float): Circle center Y
    """
    import math

    if center_x is None:
        center_x = width / 2

    positions = []
    angle_step = (2 * math.pi) / count

    for i in range(count):
        angle = i * angle_step
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        positions.append((x, y))

    return positions


def pattern_grid(count, width, y_offset=-100, cols=None, row_spacing=80, col_spacing=100, **_):
    """
    Grid formation.

    Args:
        count (int): Number of enemies
        width (int): Screen width
        y_offset (float): Top row Y position
        cols (int): Columns per row (auto-calculated if None)
        row_spacing (float): Vertical spacing between rows
        col_spacing (float): Horizontal spacing between columns
    """
    import math

    if cols is None:
        cols = math.ceil(math.sqrt(count))

    rows = math.ceil(count / cols)
    grid_width = (cols - 1) * col_spacing
    start_x = (width - grid_width) / 2

    positions = []
    for i in range(count):
        row = i // cols
        col = i % cols
        x = start_x + col * col_spacing
        y = y_offset + row * row_spacing
        positions.append((x, y))

    return positions


def pattern_single(count, width, x=None, y=-100, **_):
    """
    Single enemy spawn (or multiple at same position).

    Args:
        count (int): Number of enemies
        width (int): Screen width
        x (float): Spawn X (defaults to center)
        y (float): Spawn Y
    """
    if x is None:
        x = width / 2

    return [(x, y)] * count


# ===========================================================
# Auto-register all patterns
# ===========================================================
PatternRegistry.register("line", pattern_line)
PatternRegistry.register("v", pattern_v)
PatternRegistry.register("circle", pattern_circle)
PatternRegistry.register("grid", pattern_grid)
PatternRegistry.register("single", pattern_single)