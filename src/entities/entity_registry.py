"""
entity_registry.py
------------------
Central registry and factory for dynamic entity creation.

Responsibilities
----------------
- Maintain a global mapping of entity classes by category and type name.
- Allow other modules to register entities automatically on import.
- Provide a safe unified `create()` factory for all entity spawning.
"""

from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_types import EntityCategory
from src.core.services.config_manager import load_config


class EntityRegistry:
    """Global registry and factory for creating entities dynamically."""

    _registry = {}  # {category: {type_name: class}}
    _entity_data = {}  # {category: {type_name: data_dict}}

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
    def auto_register(cls, entity_class):
        """
        Auto-register an entity using its __registry__ attributes.
        Called automatically via __init_subclass__ in base classes.

        Validates:
        - Category and name are non-empty strings
        - Category is in EntityCategory.REGISTRY_VALID
        - No duplicate registrations (warns if overwriting)
        - Entity class is valid type
        """
        category = getattr(entity_class, '__registry_category__', None)
        name = getattr(entity_class, '__registry_name__', None)

        # Validation 1: Check attributes exist
        if not category or not name:
            # Skip base classes without registration attributes
            return

        # Validation 2: Type checking
        if not isinstance(category, str):
            DebugLogger.warn(
                f"[Registry] Invalid category type for {entity_class.__name__}: "
                f"expected str, got {type(category).__name__}"
            )
            return

        if not isinstance(name, str):
            DebugLogger.warn(
                f"[Registry] Invalid name type for {entity_class.__name__}: "
                f"expected str, got {type(name).__name__}"
            )
            return

        # Validation 3: Empty string check
        if not category.strip():
            DebugLogger.warn(
                f"[Registry] Empty category string for {entity_class.__name__}"
            )
            return

        if not name.strip():
            DebugLogger.warn(
                f"[Registry] Empty name string for {entity_class.__name__}"
            )
            return

        # Validation 4: Check category is valid
        try:
            if category not in EntityCategory.REGISTRY_VALID:
                DebugLogger.warn(
                    f"[Registry] Unknown category '{category}' for {entity_class.__name__}. "
                    f"Valid categories: {EntityCategory.REGISTRY_VALID}"
                )
                # Still allow registration for flexibility, just warn
        except ImportError:
            pass  # EntityCategory not available, skip validation

        # Validation 5: Check for duplicate registration
        existing = cls.get(category, name)

        if existing is not None and existing is not entity_class:
            DebugLogger.warn(
                f"[Registry] Overwriting [{category}:{name}]: "
                f"{existing.__name__} → {entity_class.__name__}"
            )

        # Validation 6: Verify it's a class type
        if not isinstance(entity_class, type):
            DebugLogger.warn(
                f"[Registry] {entity_class} is not a class type"
            )
            return

        # All validations passed - register
        cls.register(category, name, entity_class)

    @classmethod
    def load_entity_data(cls, config_path: str):
        """
        Load entity definitions from JSON.

        Args:
            config_path: Path to entity JSON (e.g., "entities/enemies.json")
        """

        data = load_config(config_path, default_dict={})

        # Determine category from filename
        # enemies.json -> "enemy"
        # bullets.json -> "projectile"
        filename = config_path.split('/')[-1].replace('.json', '')
        category_map = {
            "enemies": "enemy",
            "bullets": "projectile",
            "items": "pickup",
            "obstacles": "obstacle",
            "hazards": "hazard"
        }
        category = category_map.get(filename, filename)

        if category not in cls._entity_data:
            cls._entity_data[category] = {}

        cls._entity_data[category].update(data)

        DebugLogger.init_sub(
            f"Loaded {len(data)} {category} definitions"
        )

    @classmethod
    def get_data(cls, category: str, name: str) -> dict:
        """
        Retrieve entity data by category and name.

        Returns:
            dict: Entity data or empty dict if not found
        """
        return cls._entity_data.get(category, {}).get(name, {})

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

    # ===========================================================
    # Inspection & Debugging
    # ===========================================================
    @classmethod
    def list_all(cls) -> dict:
        """
        Return all registered entities organized by category.

        Returns:
            dict: {category: {name: class}}
        """
        return cls._registry.copy()

    @classmethod
    def list_category(cls, category: str) -> dict:
        """
        Return all entities in a specific category.

        Args:
            category: Category name (e.g., "enemy", "projectile")

        Returns:
            dict: {name: class}
        """
        return cls._registry.get(category, {}).copy()

    @classmethod
    def get_registered_names(cls, category: str) -> list:
        """
        Get list of all registered entity names in a category.

        Args:
            category: Category name

        Returns:
            list: Entity names in that category
        """
        return list(cls._registry.get(category, {}).keys())
