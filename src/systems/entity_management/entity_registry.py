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

    _CATEGORY_MAP = {
        "enemies": "enemy",
        "bullets": "projectile",
        "items": "pickup",
        "obstacles": "obstacle",
        "hazards": "hazard"
    }

    _REQUIRED_FIELDS = {
        'enemy': ['hp', 'speed', 'exp'],
        'projectile': ['damage', 'radius'],
        'pickup': ['effect_type', 'value']
    }

    # ===========================================================
    # Registration
    # ===========================================================
    @classmethod
    def register(cls, category: str, name: str, entity_class):
        """Register an entity class under a specific category."""
        if category not in cls._registry:
            cls._registry[category] = {}
        cls._registry[category][name] = entity_class
        DebugLogger.state(
            f"Registered entity [{category}:{name}] -> {entity_class.__name__}",
            category="loading"
        )

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
                f"expected str, got {type(category).__name__}",
                category="loading"
            )
            return

        if not isinstance(name, str):
            DebugLogger.warn(
                f"[Registry] Invalid name type for {entity_class.__name__}: "
                f"expected str, got {type(name).__name__}",
                category="loading"
            )
            return

        # Validation 3: Empty string check
        if not category.strip():
            DebugLogger.warn(
                f"[Registry] Empty category string for {entity_class.__name__}",
                category="loading"
            )
            return

        if not name.strip():
            DebugLogger.warn(
                f"[Registry] Empty name string for {entity_class.__name__}",
                category="loading"
            )
            return

        # Validation 4: Check category is valid
        try:
            if category not in EntityCategory.REGISTRY_VALID:
                DebugLogger.warn(
                    f"[Registry] Unknown category '{category}' for {entity_class.__name__}. "
                    f"Valid categories: {EntityCategory.REGISTRY_VALID}",
                    category="loading"
                )
                # Still allow registration for flexibility, just warn
        except (TypeError, AttributeError):
            pass  # EntityCategory not available, skip validation

        # Validation 5: Check for duplicate registration
        existing = cls.get(category, name)

        if existing is not None and existing is not entity_class:
            DebugLogger.warn(
                f"[Registry] Overwriting [{category}:{name}]: "
                f"{existing.__name__} → {entity_class.__name__}",
                category="loading"
            )

        # Validation 6: Verify it's a class type
        if not isinstance(entity_class, type):
            DebugLogger.warn(
                f"[Registry] {entity_class} is not a class type",
                category="loading"
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

        filename = config_path.split('/')[-1].replace('.json', '')
        category = cls._CATEGORY_MAP.get(filename, filename)
        required = cls._REQUIRED_FIELDS.get(category, [])

        for name, entity_data in data.items():
            missing = [f for f in required if f not in entity_data]
            if missing:
                DebugLogger.warn(
                    f"[Registry] Entity '{name}' missing fields: {missing}",
                    category="loading"
                )

        if category not in cls._entity_data:
            cls._entity_data[category] = {}

        cls._entity_data[category].update(data)

        DebugLogger.init_sub(
            f"Loaded {len(data)} {category} definition(s) from {filename}.json"
        )

    @classmethod
    def get_data(cls, category: str, name: str) -> dict:
        """
        Retrieve entity data by category and name.

        Args:
            category: Entity category
            name: Entity type name

        Returns:
            dict: Entity data or empty dict if not found
        """
        if category not in cls._entity_data:
            return {}

        return cls._entity_data.get(category, {}).get(name, {})

    @classmethod
    def get(cls, category: str, name: str):
        """
        Retrieve an entity class by category and name.

        Args:
            category: Entity category
            name: Entity type name

        Returns:
            Entity class or None if not found
        """
        return cls._registry.get(category, {}).get(name, None)

    @classmethod
    def has(cls, category: str, name: str) -> bool:
        """
        Check if an entity class is registered.

        Args:
            category: Entity category
            name: Entity name

        Returns:
            bool: True if entity exists in registry
        """
        return category in cls._registry and name in cls._registry[category]

    # ===========================================================
    # Factory
    # ===========================================================
    @classmethod
    def create(cls, category: str, name: str, *args, **kwargs):
        """
        Instantiate a registered entity class.

        Args:
            category: Entity category
            name: Entity type name
            *args: Positional arguments for entity constructor
            **kwargs: Keyword arguments for entity constructor

        Returns:
            Entity instance or None if creation failed
        """
        entity_cls = cls.get(category, name)
        if entity_cls is None:
            DebugLogger.warn(
                f"[Registry] Cannot create unregistered entity [{category}:{name}]",
                category="entity_spawn"
            )
            return None

        try:
            return entity_cls(*args, **kwargs)
        except TypeError as e:
            # TypeError usually means wrong arguments
            DebugLogger.warn(
                f"[Registry] Failed to create [{category}:{name}]: {e}. "
                f"Check constructor signature.",
                category="entity_spawn"
            )
            return None
        except Exception as e:
            # Other exceptions
            DebugLogger.warn(
                f"[Registry] Failed to create [{category}:{name}]: {e}",
                category="entity_spawn"
            )
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
            dict: {name: class} or empty dict if category doesn't exist
        """
        return cls._registry.get(category, {}).copy()

    @classmethod
    def get_registered_names(cls, category: str) -> list:
        """
        Get list of all registered entity names in a category.

        Args:
            category: Category name

        Returns:
            list: Entity names in that category, empty list if category doesn't exist
        """
        if category not in cls._registry:
            return []

        return list(cls._registry[category].keys())

    @classmethod
    def get_all_categories(cls) -> list:
        """
        Get list of all categories that have registered entities.

        Returns:
            list: Category names that have at least one registered entity
        """
        return [cat for cat in cls._registry.keys() if cls._registry[cat]]

    @classmethod
    def get_registry_stats(cls) -> dict:
        """
        Get statistics about the current registry state.

        Returns:
            dict: Statistics including counts per category
        """
        stats = {
            "total_categories": len(cls._registry),
            "total_entities": 0,
            "entities_per_category": {},
            "data_loaded_categories": list(cls._entity_data.keys())
        }

        for category, entities in cls._registry.items():
            count = len(entities)
            stats["entities_per_category"][category] = count
            stats["total_entities"] += count

        return stats

    @classmethod
    def validate_entity_data(cls, category: str, name: str) -> bool:
        """
        Check if entity has both class registration AND data loaded.

        Args:
            category: Entity category
            name: Entity type name

        Returns:
            bool: True if entity has both class and data
        """
        has_class = cls.has(category, name)
        has_data = bool(cls.get_data(category, name))

        if has_class and not has_data:
            DebugLogger.warn(
                f"[Registry] Entity [{category}:{name}] registered but has no JSON data",
                category="loading"
            )

        if has_data and not has_class:
            DebugLogger.warn(
                f"[Registry] Entity [{category}:{name}] has JSON data but no class registered",
                category="loading"
            )

        return has_class and has_data