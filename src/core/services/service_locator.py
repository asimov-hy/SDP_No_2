"""
service_locator.py
------------------
Centralized access to core game services and systems.
Provides dependency injection for scenes and managers.
"""

from typing import Any


# ===========================================================
# Service Locator
# ===========================================================


class ServiceLocator:
    """Container for core game services with scene-local and global registries."""

    __slots__ = (
        "scene_manager",
        "display_manager",
        "input_manager",
        "draw_manager",
        "ui_manager",
        "_global_systems",
        "_entities",
    )

    def __init__(self, scene_manager):
        """
        Initialize with core managers.

        Args:
            scene_manager: The SceneManager instance
        """
        self.scene_manager = scene_manager
        self.display_manager = None
        self.input_manager = None
        self.draw_manager = None
        self.ui_manager = None
        self._global_systems = {}
        self._entities = {}

    # ===========================================================
    # Manager Registration
    # ===========================================================

    def register_managers(self, display=None, input_mgr=None, draw=None, ui=None):
        """
        Register core managers.

        Args:
            display: DisplayManager instance
            input_mgr: InputManager instance
            draw: DrawManager instance
            ui: UIManager instance
        """
        if display:
            self.display_manager = display
        if input_mgr:
            self.input_manager = input_mgr
        if draw:
            self.draw_manager = draw
        if ui:
            self.ui_manager = ui

    # ===========================================================
    # Entity Access (Scene-Local)
    # ===========================================================

    def register_entity(self, key: str, entity: Any) -> None:
        """
        Register a gameplay entity. Cleared on scene transition.

        Args:
            key: Entity identifier (e.g., "player", "boss")
            entity: Entity instance
        """
        self._entities[key] = entity

    def get_entity(self, key: str, default: Any = None) -> Any:
        """
        Get a registered entity.

        Args:
            key: Entity identifier
            default: Value if not found

        Returns:
            Entity instance or default
        """
        return self._entities.get(key, default)

    def unregister_entity(self, key: str) -> None:
        """Remove an entity from registry."""
        self._entities.pop(key, None)

    def has_entity(self, key: str) -> bool:
        """Check if entity is registered."""
        return key in self._entities

    # ===========================================================
    # Entity Shortcuts
    # ===========================================================

    @property
    def player(self) -> Any:
        """Quick access to player entity."""
        return self._entities.get("player")

    @property
    def boss(self) -> Any:
        """Quick access to boss entity."""
        return self._entities.get("boss")

    # ===========================================================
    # Global System Access
    # ===========================================================

    def register_global(self, name: str, system: Any) -> None:
        """
        Register a system that persists across scenes.

        Args:
            name: System identifier
            system: System instance
        """
        self._global_systems[name] = system

    def get_global(self, name: str, default: Any = None) -> Any:
        """
        Get a global system by name.

        Args:
            name: System identifier
            default: Value if not found

        Returns:
            System instance or default
        """
        return self._global_systems.get(name, default)

    def has_global(self, name: str) -> bool:
        """Check if global system is registered."""
        return name in self._global_systems

    def unregister_global(self, name: str) -> None:
        """Remove a global system."""
        self._global_systems.pop(name, None)

    # ===========================================================
    # Lifecycle
    # ===========================================================

    def clear_entities(self) -> None:
        """Clear all scene-local entities. Called on scene exit."""
        self._entities.clear()

    def clear_globals(self) -> None:
        """Clear all global systems. Use on full shutdown only."""
        self._global_systems.clear()

    def clear_all(self) -> None:
        """Clear both entities and globals."""
        self._entities.clear()
        self._global_systems.clear()

    # ===========================================================
    # Scene Transition
    # ===========================================================

    def transition_to(self, scene_name: str, transition=None, **scene_data) -> None:
        """
        Convenience method for scene transitions.

        Args:
            scene_name: Target scene identifier
            transition: Optional transition effect
            **scene_data: Data to pass to next scene
        """
        self.scene_manager.set_scene(scene_name, transition, **scene_data)
