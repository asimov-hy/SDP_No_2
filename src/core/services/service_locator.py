"""
service_locator.py
------------------
Centralized access to core game services and systems.
Provides dependency injection for scenes and controllers.
"""

class ServiceLocator:
    """
    Container for core game services.
    Provides domain-specific API for common access patterns.
    """
    __slots__ = (
        'scene_manager', 'display_manager', 'input_manager',
        'draw_manager', 'ui_manager', '_global_systems', '_entities'
    )

    def __init__(self, scene_manager):
        """
        Initialize with core managers from scene_manager.

        Args:
            scene_manager: The SceneManager instance
        """
        # Core managers (always available)
        self.scene_manager = scene_manager

        # Validate required managers exist
        required = ['display', 'input_manager', 'draw_manager', 'ui_manager']
        for attr in required:
            if not hasattr(scene_manager, attr):
                raise ValueError(f"SceneManager missing required attribute: {attr}")

        self.display_manager = scene_manager.display
        self.input_manager = scene_manager.input_manager
        self.draw_manager = scene_manager.draw_manager
        self.ui_manager = scene_manager.ui_manager

        # Global systems (persist across scenes)
        self._global_systems = {}

        # Scene-local entities (cleared on scene exit)
        self._entities = {}

    # ===========================================================
    # Entity Access (Scene-Local)
    # ===========================================================

    def register_entity(self, key: str, entity):
        """
        Register a gameplay entity for cross-system access.
        Scene-local - cleared on scene transition.

        Args:
            key: Entity identifier (e.g., "player", "boss")
            entity: Entity instance

        Example:
            services.register_entity("player", player)
        """
        self._entities[key] = entity

    def get_entity(self, key: str, default=None):
        """
        Get a registered entity safely.

        Args:
            key: Entity identifier
            default: Value to return if key not found

        Returns:
            Entity instance or default

        Example:
            player = services.get_entity("player")
        """
        return self._entities.get(key, default)

    def unregister_entity(self, key: str):
        """
        Remove an entity from registry.

        Args:
            key: Entity identifier
        """
        if key in self._entities:
            del self._entities[key]

    def has_entity(self, key: str) -> bool:
        """
        Check if entity is registered.

        Args:
            key: Entity identifier

        Returns:
            bool: True if entity exists
        """
        return key in self._entities

    # ===========================================================
    # Global System Access
    # ===========================================================

    def register_global(self, name: str, system):
        """
        Register a system that persists across scene changes.

        Args:
            name: System identifier (e.g., "entity_registry", "level_registry")
            system: System instance

        Example:
            services.register_global("entity_registry", EntityRegistry)
        """
        self._global_systems[name] = system

    def get_global(self, name: str, default=None):
        """
        Get a global system by name.

        Args:
            name: System identifier
            default: Value to return if not found

        Returns:
            System instance or default

        Example:
            registry = services.get_global("entity_registry")
        """
        return self._global_systems.get(name, default)

    def has_global(self, name: str) -> bool:
        """
        Check if global system is registered.

        Args:
            name: System identifier

        Returns:
            bool: True if system exists
        """
        return name in self._global_systems

    # ===========================================================
    # Lifecycle Management
    # ===========================================================

    def clear_entities(self):
        """
        Clear all scene-local entities.
        Called automatically on scene exit.
        """
        self._entities.clear()

    def clear_globals(self):
        """Clear all global systems. Use with caution - typically only on full shutdown."""
        self._global_systems.clear()

    # ===========================================================
    # Scene Transition Convenience
    # ===========================================================

    def transition_to(self, scene_name: str, transition=None, **scene_data):
        """
        Convenience method for scene transitions.

        Args:
            scene_name: Target scene identifier
            transition: Optional transition effect
            **scene_data: Data to pass to next scene

        Example:
            services.transition_to("GameScene", level="demo_level")
        """
        self.scene_manager.set_scene(scene_name, transition, **scene_data)
