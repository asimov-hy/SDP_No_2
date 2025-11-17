"""
system_initializer.py
---------------------
Abstract base class for system initialization.
Separates system setup logic from scene construction.
"""

from abc import ABC, abstractmethod


class SystemInitializer(ABC):
    """
    Base class for initializing game systems.

    Subclasses define which systems to create and how to wire them together.
    Systems are registered with ServiceLocator for cross-system access.
    """

    def __init__(self, services):
        """
        Initialize with service locator.

        Args:
            services: ServiceLocator instance
        """
        self.services = services

        # Convenience access to managers
        self.display = services.display_manager
        self.input_manager = services.input_manager
        self.draw_manager = services.draw_manager

    @abstractmethod
    def initialize(self) -> dict:
        """
        Initialize all systems for this configuration.

        Returns:
            dict: System instances keyed by name
            Example: {"player": player, "ui": ui_manager, ...}

        Implementation should:
        1. Create system instances
        2. Wire dependencies between systems
        3. Register systems with services (if needed globally)
        4. Return dict of systems for scene access
        """
        pass