"""
binding_system.py
-----------------
Resolves data bindings for dynamic ui updates.
"""

from typing import Any, Dict, List, Optional


class BindingSystem:
    """Manages data bindings between ui elements and game objects."""

    def __init__(self):
        """Initialize empty binding context."""
        self.context: Dict[str, Any] = {}
        self._path_cache: Dict[str, List[str]] = {}  # Cache split paths

    def register(self, name: str, obj: Any):
        """
        Register an object to be accessible in bindings.

        Args:
            name: Name to reference in bind paths (e.g., 'player')
            obj: Object to bind to
        """
        self.context[name] = obj

    def unregister(self, name: str):
        """
        Remove a registered object.

        Args:
            name: Name to remove
        """
        if name in self.context:
            del self.context[name]

    def resolve(self, path: str) -> Optional[Any]:
        """
        Resolve a binding path to its current value.

        Args:
            path: Dot-separated path (e.g., 'player.health', 'boss.active')

        Returns:
            Current value or None if path doesn't exist
        """
        if not path:
            return None

        # Use cached path parts
        if path not in self._path_cache:
            self._path_cache[path] = path.split('.')
        parts = self._path_cache[path]

        # Get root object
        obj = self.context.get(parts[0])
        if obj is None:
            return None

        # Navigate path
        for part in parts[1:]:
            obj = getattr(obj, part, None)
            if obj is None:
                return None

        return obj

    def evaluate_condition(self, path: str, condition: str) -> bool:
        """
        Evaluate a conditional binding.

        Args:
            path: Binding path
            condition: Condition string (e.g., '< 50', '> 0', '== True')

        Returns:
            True if condition is met, False otherwise
        """
        value = self.resolve(path)
        if value is None:
            return False

        # Parse condition
        condition = condition.strip()

        # Simple comparison operators
        if condition.startswith('<='):
            threshold = float(condition[2:].strip())
            return value <= threshold
        elif condition.startswith('>='):
            threshold = float(condition[2:].strip())
            return value >= threshold
        elif condition.startswith('<'):
            threshold = float(condition[1:].strip())
            return value < threshold
        elif condition.startswith('>'):
            threshold = float(condition[1:].strip())
            return value > threshold
        elif condition.startswith('=='):
            target = condition[2:].strip()
            # Handle boolean strings
            if target.lower() == 'true':
                return bool(value)
            elif target.lower() == 'false':
                return not bool(value)
            # Handle numeric comparison
            try:
                return value == float(target)
            except ValueError:
                return str(value) == target
        elif condition.startswith('!='):
            target = condition[2:].strip()
            if target.lower() == 'true':
                return not bool(value)
            elif target.lower() == 'false':
                return bool(value)
            try:
                return value != float(target)
            except ValueError:
                return str(value) != target

        # Default: treat as boolean
        return bool(value)