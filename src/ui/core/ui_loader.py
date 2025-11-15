"""
ui_loader.py
------------
Loads ui configurations from YAML files and instantiates element trees.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from .ui_element import UIElement

# Element type registry
ELEMENT_REGISTRY = {}


def register_element(type_name: str):
    """Decorator to register element types."""

    def decorator(cls):
        ELEMENT_REGISTRY[type_name] = cls
        return cls

    return decorator


class UILoader:
    """Loads and parses ui configurations from YAML files."""

    def __init__(self, ui_manager, theme_manager=None):
        """
        Initialize loader.

        Args:
            ui_manager: Reference to UIManager
            theme_manager: Optional theme manager for style application
        """
        self.ui_manager = ui_manager
        self.theme_manager = theme_manager
        self.cache: Dict[str, Dict] = {}
        self.base_path = Path("src/ui/configs")

    def load(self, filename: str) -> UIElement:
        """
        Load ui configuration from YAML file.

        Args:
            filename: Path to YAML file relative to ui/configs/

        Returns:
            Root UIElement
        """
        # Check cache
        if filename in self.cache:
            return self._instantiate(self.cache[filename])

        # Load file
        full_path = self.base_path / filename

        if not full_path.exists():
            raise FileNotFoundError(f"ui config not found: {full_path}")

        with open(full_path, 'r') as f:
            config = yaml.safe_load(f)

        # Cache parsed config
        self.cache[filename] = config

        return self._instantiate(config)

    def load_from_dict(self, config: Dict[str, Any]) -> UIElement:
        """
        Load ui from dictionary (for programmatic creation).

        Args:
            config: Configuration dictionary

        Returns:
            Root UIElement
        """
        return self._instantiate(config)

    def _instantiate(self, config: Dict[str, Any], parent=None) -> UIElement:
        """
        Recursively instantiate ui element tree from config.

        Args:
            config: Configuration dictionary
            parent: Parent element (for children)

        Returns:
            Instantiated UIElement
        """
        # Handle root-level named configs
        if len(config) == 1 and not 'type' in config:
            # Root element with name (e.g., "pause_menu: ...")
            root_key = list(config.keys())[0]
            element_config = config[root_key]
        else:
            element_config = config

        # Apply theme/style if specified
        if self.theme_manager and 'style' in element_config:
            element_config = self.theme_manager.apply_style(element_config.copy())

        # Get element type
        element_type = element_config.get('type', 'element')

        # Lazy import element class
        element_class = self._get_element_class(element_type)

        # Create element
        element = element_class(element_config)
        element.parent = parent

        # Process children
        children = element_config.get('children', [])
        for child_config in children:
            child = self._instantiate(child_config, parent=element)

            # Add to parent if it's a container
            if hasattr(element, 'add_child'):
                element.add_child(child)

        return element

    def clear_cache(self):
        """Clear the configuration cache."""
        self.cache.clear()

    def _get_element_class(self, element_type: str):
        """Resolve element classes via lazy import."""
        # Already registered?
        if element_type in ELEMENT_REGISTRY:
            return ELEMENT_REGISTRY[element_type]

        # Lazy-import element types
        if element_type == "button":
            from ..elements.button import UIButton
            return UIButton
        elif element_type == "label":
            from ..elements.label import UILabel
            return UILabel
        elif element_type == "bar":
            from ..elements.bar import UIBar
            return UIBar
        elif element_type == "container":
            from ..elements.container import UIContainer
            return UIContainer

        # Fallback
        return UIElement



# Register base element type
register_element('element')(UIElement)