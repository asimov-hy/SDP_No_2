"""
entity_registry.py
------------------
Central registry and factory for dynamic entity creation.

Responsibilities
----------------
- Maintain a global mapping of entity classes by category and type name.
- Allow other modules to register entities_animation automatically on import.
- Provide a safe unified `create()` factory for all entity spawning.
"""

from src.core.debug.debug_logger import DebugLogger


class EntityRegistry:
    """Global registry and factory for creating entities_animation dynamically."""

    _registry = {}  # {category: {type_name: class}}

    # ===========================================================
    # Registration
    # ===========================================================
    @classmethod
    def register(cls, category: str, name: str, entity_class):
        """Register an entity class under a specific category."""
        if category not in cls._registry:
            cls._registry[category] = {}
        cls._registry[category][name] = entity_class
        DebugLogger.state(f"[Registry] Registered entity [{category}:{name}]", category="loading")

    @classmethod
    def get(cls, category: str, name: str):
        """Retrieve an entity class by category and name."""
        return cls._registry.get(category, {}).get(name, None)

    # ===========================================================
    # Factory
    # ===========================================================
    @classmethod
    def create(cls, category: str, name: str, *args, **kwargs):
        """Instantiate a registered entity class."""
        entity_cls = cls.get(category, name)
        if entity_cls is None:
            DebugLogger.warn(f"[Registry] Unknown entity [{category}:{name}]")
            return None

        try:
            return entity_cls(*args, **kwargs)
        except Exception as e:
            DebugLogger.warn(f"[Registry] Failed to create [{category}:{name}] → {e}")
            return None
