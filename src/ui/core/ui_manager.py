"""
ui_manager.py
-------------
Manages ui screens, HUD elements, and rendering with the new system.
"""

import pygame
from typing import Dict, List, Optional, Tuple

from src.ui.core.anchor_resolver import AnchorResolver
from .binding_system import BindingSystem
from .ui_loader import UILoader
from .ui_element import UIElement


class UIManager:
    """Manages all ui elements, screens, and rendering."""

    def __init__(self, display_manager, draw_manager, game_width: int = 1280, game_height: int = 720):
        """
        Initialize ui manager.

        Args:
            display_manager: Reference to DisplayManager
            draw_manager: Reference to DrawManager
            game_width: Logical game width
            game_height: Logical game height
        """
        self.display = display_manager
        self.draw_manager = draw_manager

        # Core systems
        self.anchor_resolver = AnchorResolver(game_width, game_height)
        self.bindings = BindingSystem()
        self.loader = UILoader(self)

        # ui organization
        self.screens: Dict[str, UIElement] = {}  # Named screens (pause, settings, etc)
        self.active_screen: Optional[str] = None
        self.hud_elements: List[UIElement] = []  # Persistent HUD overlay

        # State
        self.modal_stack: List[str] = []  # Stack of active modal screens

    # ===================================================================
    # DrawManager Integration
    # ===================================================================

    def _inject_draw_manager_to_tree(self, element: UIElement):
        """Recursively inject DrawManager reference to element tree."""
        element.set_draw_manager(self.draw_manager)
        if hasattr(element, 'children'):
            for child in element.children:
                self._inject_draw_manager_to_tree(child)

    # ===================================================================
    # Screen Management
    # ===================================================================
    def register_screen(self, name: str, root_element: UIElement):
        """
        Register a ui screen.

        Args:
            name: Screen identifier
            root_element: Root element of the screen
        """
        self.screens[name] = root_element
        self._inject_draw_manager_to_tree(root_element)

    def load_screen(self, name: str, filename: str):
        """
        Load and register a screen from YAML file.

        Args:
            name: Screen identifier
            filename: YAML file path relative to ui/configs/
        """
        root_element = self.loader.load(filename)
        self.register_screen(name, root_element)

    def show_screen(self, name: str, modal: bool = False):
        """
        Show a screen.

        Args:
            name: Screen identifier
            modal: If True, push onto modal stack (can stack multiple)
        """
        if name not in self.screens:
            return

        if modal:
            self.modal_stack.append(name)
        else:
            # Hide previous active screen
            if self.active_screen:
                self._on_screen_hide(self.active_screen)

            self.active_screen = name
            self._on_screen_show(name)

    def hide_screen(self, name: Optional[str] = None):
        """
        Hide a screen.

        Args:
            name: Screen to hide. If None, hides active screen.
        """
        if name is None:
            name = self.active_screen

        if not name:
            return

        # Remove from modal stack if present
        if name in self.modal_stack:
            self.modal_stack.remove(name)

        # Clear active screen if it's the one being hidden
        if name == self.active_screen:
            self._on_screen_hide(name)
            self.active_screen = None

    def toggle_screen(self, name: str):
        """Toggle screen visibility."""
        if name == self.active_screen or name in self.modal_stack:
            self.hide_screen(name)
        else:
            self.show_screen(name)

    def _on_screen_show(self, name: str):
        """Called when screen is shown."""
        screen = self.screens.get(name)
        if screen and hasattr(screen, 'on_show'):
            screen.on_show()

    def _on_screen_hide(self, name: str):
        """Called when screen is hidden."""
        screen = self.screens.get(name)
        if screen and hasattr(screen, 'on_hide'):
            screen.on_hide()

    # ===================================================================
    # HUD Management
    # ===================================================================

    def register_hud(self, element: UIElement):
        """
        Register a persistent HUD element.

        Args:
            element: HUD element to add
        """
        self.hud_elements.append(element)

    def load_hud(self, filename: str):
        """
        Load and register HUD from YAML file.

        Args:
            filename: YAML file path relative to ui/configs/
        """
        root_element = self.loader.load(filename)

        # If root is a container, add all children as separate HUD elements
        if hasattr(root_element, 'children'):
            for child in root_element.children:
                self.register_hud(child)
        else:
            self.register_hud(root_element)

    def clear_hud(self):
        """Remove all HUD elements."""
        self.hud_elements.clear()

    # ===================================================================
    # Element Lookup
    # ===================================================================

    def find_element_by_id(self, screen_name: str, element_id: str):
        """
        Find element by id in a screen.

        Args:
            screen_name: Screen to search in
            element_id: Element id to find

        Returns:
            UIElement or None
        """
        screen = self.screens.get(screen_name)
        if not screen:
            return None
        return self._find_in_tree(screen, element_id)

    def _find_in_tree(self, element, target_id: str):
        """Recursive element search by id."""
        # Check element.id attribute
        if getattr(element, 'id', None) == target_id:
            return element
        # Check config dict id
        if getattr(element, 'config', {}).get('id') == target_id:
            return element
        # Recurse children
        for child in getattr(element, 'children', []):
            result = self._find_in_tree(child, target_id)
            if result:
                return result
        return None

    # ===================================================================
    # Binding Management
    # ===================================================================

    def register_binding(self, name: str, obj):
        """
        Register an object for data binding.

        Args:
            name: Binding name (e.g., 'player', 'boss')
            obj: Object to bind
        """
        self.bindings.register(name, obj)

    def unregister_binding(self, name: str):
        """Remove a binding."""
        self.bindings.unregister(name)

    # ===================================================================
    # Update & Input
    # ===================================================================

    def update(self, dt: float, mouse_pos: Tuple[int, int]):
        """
        Update all active ui elements.

        Args:
            dt: Delta time in seconds
            mouse_pos: Current mouse position
        """
        # Update HUD (always active)
        for element in self.hud_elements:
            self._update_element_tree(element, dt, mouse_pos)

        # Update modal screens (from bottom to top)
        for screen_name in self.modal_stack:
            screen = self.screens.get(screen_name)
            if screen:
                self._update_element_tree(screen, dt, mouse_pos)

        # Update active screen
        if self.active_screen:
            screen = self.screens.get(self.active_screen)
            if screen:
                self._update_element_tree(screen, dt, mouse_pos)

    def _update_element_tree(self, element: UIElement, dt: float, mouse_pos: Tuple[int, int]):
        """Recursively update element and children."""
        if not element.visible:
            return

        # Update this element
        element.update(dt, mouse_pos, self.bindings)

        # Update children
        if hasattr(element, 'children'):
            for child in element.children:
                self._update_element_tree(child, dt, mouse_pos)

    def handle_event(self, event) -> Optional[str]:
        """
        Handle input events.

        Args:
            event: Pygame event

        Returns:
            Action string if an element was activated, None otherwise
        """
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        mouse_pos = event.pos

        # Check modal screens first (top to bottom)
        for screen_name in reversed(self.modal_stack):
            screen = self.screens.get(screen_name)
            if screen:
                action = self._handle_click_tree(screen, mouse_pos)
                if action:
                    return action

        # Check active screen
        if self.active_screen:
            screen = self.screens.get(self.active_screen)
            if screen:
                action = self._handle_click_tree(screen, mouse_pos)
                if action:
                    return action

        # Check HUD
        for element in self.hud_elements:
            action = self._handle_click_tree(element, mouse_pos)
            if action:
                return action

        return None

    def _handle_click_tree(self, element: UIElement, mouse_pos: Tuple[int, int]) -> Optional[str]:
        """Recursively check element tree for clicks."""
        if not element.visible or not element.enabled:
            return None

        # Check this element
        if element.rect and element.rect.collidepoint(mouse_pos):
            action = element.handle_click(mouse_pos)
            if action:
                return action

        # Check children (front to back)
        if hasattr(element, 'children'):
            for child in reversed(element.children):
                action = self._handle_click_tree(child, mouse_pos)
                if action:
                    return action

        return None

    # ===================================================================
    # Rendering
    # ===================================================================

    def draw(self, draw_manager):
        """
        Render all visible ui elements.

        Args:
            draw_manager: DrawManager instance
        """
        # Draw HUD (bottom layer)
        for element in self.hud_elements:
            self._draw_element_tree(element, draw_manager)

        # Draw active screen
        if self.active_screen:
            screen = self.screens.get(self.active_screen)
            if screen:
                self._draw_element_tree(screen, draw_manager)

        # Draw modal screens (bottom to top)
        for screen_name in self.modal_stack:
            screen = self.screens.get(screen_name)
            if screen:
                self._draw_element_tree(screen, draw_manager)

    def _draw_element_tree(self, element, draw_manager, parent=None):
        """Recursively draw element and children."""
        if not element.visible:
            return

        # NEW: Only resolve position if cache is invalid
        # Parent invalidation cascades to children since their anchors may be relative
        parent_invalid = parent and not getattr(parent, '_position_cache_valid', True)

        if not element._position_cache_valid or parent_invalid:
            element.rect = self.anchor_resolver.resolve(element, parent)
            element._position_cache_valid = True

        # Register element if it has an ID (BEFORE children)
        if element.id:
            self.anchor_resolver.register_element(element.id, element)

        # Render surface
        surface = element.render_surface()

        # Queue for drawing
        draw_manager.queue_draw(surface, element.rect, element.layer)

        # Draw children
        if hasattr(element, 'children'):
            for child in element.children:
                self._draw_element_tree(child, draw_manager, parent=element)