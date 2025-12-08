"""
ui_manager.py
-------------
Manages ui screens, HUD elements, and rendering with the new system.
"""

import pygame
from typing import Dict, List, Optional, Tuple

from src.core.runtime.game_settings import Layers
from src.ui.core.anchor_resolver import AnchorResolver

from .binding_system import BindingSystem
from .ui_loader import UILoader
from .ui_element import UIElement

from src.audio.sound_manager import get_sound_manager
from src.scenes.transitions.transitions import UISlideAnimation


class UIManager:
    """Manages all ui elements, screens, and rendering."""

    def __init__(
        self,
        display_manager,
        draw_manager,
        input_manager=None,
        game_width: int = 1280,
        game_height: int = 720,
    ):
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
        self.input_manager = input_manager

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
        self._screen_animations: Dict[str, "UISlideAnimation"] = {}  # Active animations
        self._pending_hides: Dict[str, bool] = {}

        # HUD slide animation tracking
        self._hud_sliding = False

        # Focus navigation
        self.focusables: List[UIElement] = []  # Flat list of focusable buttons
        self.focus_index: int = -1  # -1 = none focused

        self._pending_action: Optional[str] = None

    # ===================================================================
    # DrawManager Integration
    # ===================================================================

    def _inject_draw_manager_to_tree(self, element: UIElement):
        """Recursively inject DrawManager reference to element tree."""
        element.set_draw_manager(self.draw_manager)
        if hasattr(element, "children"):
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

    def show_screen(
        self,
        name: str,
        modal: bool = False,
        slide_from: str = None,
        slide_duration: float = 0.3,
    ):
        """
        Show a screen.

        Args:
            name: Screen identifier
            modal: If True, show as overlay on top of current screen
            slide_from: Optional slide direction ('top', 'bottom', 'left', 'right')
            slide_duration: Slide animation duration in seconds
        """
        if name not in self.screens:
            return

        screen = self.screens.get(name)

        # Auto-assign layer based on modal state
        if modal:
            self._set_auto_layer(screen, Layers.MODAL)
            self.modal_stack.append(name)
        else:
            self._set_auto_layer(screen, Layers.UI)
            if self.active_screen:
                self._on_screen_hide(self.active_screen)

            self.active_screen = name
            self._on_screen_show(name)

        # Invalidate position when showing
        if screen:
            screen.invalidate_position()

        # Start slide animation if specified
        if slide_from:
            self._screen_animations[name] = UISlideAnimation(slide_from, slide_duration)

        # Rebuild focus list when showing screen
        self.rebuild_focus_list()

    def hide_screen(
        self,
        name: Optional[str] = None,
        slide_to: str = None,
        slide_duration: float = 0.3,
    ):
        """
        Hide a screen.

        Args:
            name: Screen to hide
            slide_to: Optional slide direction ('top', 'bottom', 'left', 'right')
            slide_duration: Slide animation duration
        """
        if name is None:
            name = self.active_screen

        if not name:
            return

        # Start slide-out animation if specified
        if slide_to:
            self._screen_animations[name] = UISlideAnimation(
                slide_to, slide_duration, reverse=True
            )
            # Delay actual hide until animation completes
            self._pending_hides[name] = True
            return

        # Immediate hide
        self._do_hide_screen(name)

    def _do_hide_screen(self, name: str):
        """Actually hide the screen (after animation)."""
        if name in self.modal_stack:
            self.modal_stack.remove(name)

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
        if screen and hasattr(screen, "on_show"):
            screen.on_show()

    def _on_screen_hide(self, name: str):
        """Called when screen is hidden."""
        screen = self.screens.get(name)
        if screen and hasattr(screen, "on_hide"):
            screen.on_hide()

    # ===================================================================
    # Focus Navigation
    # ===================================================================

    def _collect_focusables(self, element: UIElement, result: List):
        """Recursively collect all focusable elements (buttons)."""
        if not element.visible or not element.enabled:
            return

        # Check if element is focusable (has action = is a button)
        if hasattr(element, "action") and element.action:
            result.append(element)

        # Recurse children
        if hasattr(element, "children"):
            for child in element.children:
                self._collect_focusables(child, result)

    def rebuild_focus_list(self):
        """Rebuild focusables list for current screen."""
        self.focusables.clear()
        self.focus_index = -1

        # Collect from modals first (top priority)
        for screen_name in reversed(self.modal_stack):
            screen = self.screens.get(screen_name)
            if screen:
                self._collect_focusables(screen, self.focusables)
                return  # Only use topmost modal

        # Otherwise collect from active screen
        if self.active_screen:
            screen = self.screens.get(self.active_screen)
            if screen:
                self._collect_focusables(screen, self.focusables)

    def navigate(self, direction: int):
        """
        Navigate focus by direction.

        Args:
            direction: -1 for up/left, +1 for down/right
        """
        if not self.focusables:
            self.rebuild_focus_list()

        if not self.focusables:
            return

        # Clear old focus
        if 0 <= self.focus_index < len(self.focusables):
            self.focusables[self.focus_index].is_focused = False

        # Move focus
        if self.focus_index < 0:
            self.focus_index = 0 if direction > 0 else len(self.focusables) - 1
        else:
            self.focus_index = (self.focus_index + direction) % len(self.focusables)

        # Set new focus
        self.focusables[self.focus_index].is_focused = True
        self.focusables[self.focus_index].mark_dirty()

    def transfer_hover_to_focus(self):
        """Find hovered button and set focus to it."""
        for i, element in enumerate(self.focusables):
            if hasattr(element, "is_hovered") and element.is_hovered:
                self.focus_index = i
                element.is_focused = True
                element.mark_dirty()
                return

    def clear_focus(self):
        """Clear keyboard focus (when mouse moves)."""
        if 0 <= self.focus_index < len(self.focusables):
            self.focusables[self.focus_index].is_focused = False
            self.focusables[self.focus_index].mark_dirty()
        self.focus_index = -1

    def activate_focused(self) -> Optional[str]:
        """Activate the currently focused element."""
        if 0 <= self.focus_index < len(self.focusables):
            element = self.focusables[self.focus_index]
            if hasattr(element, "action"):
                get_sound_manager().play_bfx("button_click")
                return element.action
        return None

    def _handle_navigation(self):
        """Process keyboard/controller UI navigation."""
        inp = self.input_manager

        # Up/Left = previous, Down/Right = next
        if inp.action_pressed("navigate_up") or inp.action_pressed("navigate_left"):
            self.transfer_hover_to_focus()
            self.navigate(-1)
        elif inp.action_pressed("navigate_down") or inp.action_pressed(
            "navigate_right"
        ):
            self.transfer_hover_to_focus()
            self.navigate(1)

        # Confirm activates focused button
        if inp.action_pressed("confirm"):
            action = self.activate_focused()
            if action:
                self._pending_action = action

        # Clear focus when mouse moves
        if inp.mouse_enabled and self.focus_index >= 0:
            self.clear_focus()

    def pop_action(self) -> Optional[str]:
        """Get and clear pending keyboard action."""
        action = self._pending_action
        self._pending_action = None
        return action

    # ===================================================================
    # HUD Management
    # ===================================================================

    def register_hud(self, element: UIElement):
        """
        Register a persistent HUD element.

        Args:
            element: HUD element to add
        """
        self._inject_draw_manager_to_tree(element)
        self.hud_elements.append(element)

    def load_hud(self, filename: str):
        """
        Load and register HUD from YAML file.

        Args:
            filename: YAML file path relative to ui/configs/
        """
        root_element = self.loader.load(filename)

        # Inject DrawManager for image loading
        self._inject_draw_manager_to_tree(root_element)

        # Auto-assign UI layer for HUD elements
        self._set_auto_layer(root_element, Layers.UI)

        # If root is a container, add all children as separate HUD elements
        if hasattr(root_element, "children"):
            for child in root_element.children:
                self.register_hud(child)
        else:
            self.register_hud(root_element)

    def clear_hud(self):
        """Remove all HUD elements."""
        self.hud_elements.clear()

    # ===================================================================
    # HUD Animation
    # ===================================================================

    ANCHOR_TO_OFFSET = {
        "top_left": (-150, -100),
        "top_center": (0, -100),
        "top_right": (150, -100),
        "center_left": (-150, 0),
        "center": (0, 0),
        "center_right": (150, 0),
        "bottom_left": (-150, 100),
        "bottom_center": (0, 100),
        "bottom_right": (150, 100),
    }

    def slide_in_hud(self, duration: float = 0.4, stagger: float = 0.15):
        """
        Slide all HUD elements from their anchor edges.

        Args:
            duration: Animation duration per element
            stagger: Delay between each element
        """
        elements = self._get_sorted_hud_elements()
        animated_count = 0

        for i, element in enumerate(elements):
            # Skip children that slide with parent (only if parent has real offset)
            if element.slide_with_parent and element.parent:
                parent_anchor = getattr(element.parent, "parent_anchor", "center")
                parent_offset = self.ANCHOR_TO_OFFSET.get(parent_anchor, (0, 0))
                if parent_offset != (0, 0):
                    continue

            # Resolve rect if not yet resolved (needed for offset calculation)
            if not element.rect:
                element.rect = self.anchor_resolver.resolve(element, None)

            anchor = getattr(element, "parent_anchor", "center")
            offset = self.ANCHOR_TO_OFFSET.get(anchor, (0, -100))
            delay = animated_count * stagger
            element.start_slide_in(offset, duration, delay)
            animated_count += 1

        self._hud_sliding = True

    def _get_sorted_hud_elements(self) -> List[UIElement]:
        """Get HUD elements sorted by position (top-left to bottom-right)."""
        elements = []
        self._flatten_elements(self.hud_elements, elements)
        # Sort by Y then X for natural top-to-bottom, left-to-right order
        elements.sort(
            key=lambda e: (e.rect.y if e.rect else 0, e.rect.x if e.rect else 0)
        )
        return elements

    def _flatten_elements(self, items: List, result: List):
        """Recursively flatten element tree."""
        for item in items:
            result.append(item)
            if hasattr(item, "children"):
                self._flatten_elements(item.children, result)

    def has_active_hud_animations(self) -> bool:
        """Check if any HUD elements are still animating."""
        if not self._hud_sliding:
            return False

        elements = []
        self._flatten_elements(self.hud_elements, elements)

        for element in elements:
            if element.is_sliding:
                return True

        self._hud_sliding = False
        return False

    def update_hud_animations(self, dt: float):
        """Update all HUD slide animations."""
        elements = []
        self._flatten_elements(self.hud_elements, elements)

        for element in elements:
            element.update_slide(dt)

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
        # Single ID check
        if element.id == target_id:
            return element

        # Recurse children
        if hasattr(element, "children"):
            for child in element.children:
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
        # Update HUD animations
        self.update_hud_animations(dt)

        # Handle keyboard/controller navigation
        if self.input_manager:
            self._handle_navigation()

        # Update screen animations
        completed = []
        for name, anim in self._screen_animations.items():
            if anim.update(dt):
                completed.append(name)
        for name in completed:
            del self._screen_animations[name]
            # Complete pending hides after slide-out
            if name in self._pending_hides:
                del self._pending_hides[name]
                self._do_hide_screen(name)

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

    def _update_element_tree(
        self, element: UIElement, dt: float, mouse_pos: Tuple[int, int]
    ):
        """Recursively update element and children."""
        if not element.visible:
            return

        # Update this element
        element.update(dt, mouse_pos, self.bindings)

        # Update children
        if hasattr(element, "children"):
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
        # Check for pending keyboard action first
        if self._pending_action:
            action = self._pending_action
            self._pending_action = None
            return action

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        mouse_pos = self.display.screen_to_game_pos(*event.pos)
        action = None

        # Check modal screens first (top to bottom)
        for screen_name in reversed(self.modal_stack):
            screen = self.screens.get(screen_name)
            if screen:
                action = self._handle_click_tree(screen, mouse_pos)
                if action:
                    break

        # Check active screen
        if not action and self.active_screen:
            screen = self.screens.get(self.active_screen)
            if screen:
                action = self._handle_click_tree(screen, mouse_pos)

        # Check HUD
        if not action:
            for element in self.hud_elements:
                action = self._handle_click_tree(element, mouse_pos)
                if action:
                    break

        if action:
            button_sound = get_sound_manager()
            button_sound.play_bfx("button_click")
        return action

    def _handle_click_tree(
        self, element: UIElement, mouse_pos: Tuple[int, int]
    ) -> Optional[str]:
        """Recursively check element tree for clicks."""
        if not element.visible or not element.enabled:
            return None

        # Check this element
        if element.rect and element.rect.collidepoint(mouse_pos):
            action = element.handle_click(mouse_pos)
            if action:
                return action

        # Check children (front to back)
        if hasattr(element, "children"):
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
                offset = self._screen_animations.get(self.active_screen, None)
                anim_offset = offset.offset if offset else (0, 0)
                self._draw_element_tree(screen, draw_manager, anim_offset=anim_offset)

        # Draw modal screens (bottom to top)
        for screen_name in self.modal_stack:
            screen = self.screens.get(screen_name)
            if screen:
                offset = self._screen_animations.get(screen_name, None)
                anim_offset = offset.offset if offset else (0, 0)
                self._draw_element_tree(screen, draw_manager, anim_offset=anim_offset)

    def _draw_element_tree(
        self, element, draw_manager, parent=None, anim_offset=(0, 0)
    ):
        """Recursively draw element and children."""
        if not element.visible:
            return

        # Only resolve position if cache is invalid
        parent_invalid = parent and not getattr(parent, "_position_cache_valid", True)

        if not element._position_cache_valid or parent_invalid:
            element.rect = self.anchor_resolver.resolve(element, parent)
            element._position_cache_valid = True

        # Register element if it has an ID (BEFORE children)
        if element.id:
            self.anchor_resolver.register_element(element.id, element)

        # Render surface
        surface = element.render_surface()

        # Apply animation offset + element slide offset to draw position
        slide = element.slide_offset
        draw_rect = element.rect.move(
            anim_offset[0] + slide[0], anim_offset[1] + slide[1]
        )

        # Queue for drawing
        draw_manager.queue_draw(surface, draw_rect, element.layer)

        # Draw children (pass offset down)
        if hasattr(element, "children"):
            combined_offset = (anim_offset[0] + slide[0], anim_offset[1] + slide[1])
            for child in element.children:
                child_offset = (
                    combined_offset if child.slide_with_parent else anim_offset
                )
                self._draw_element_tree(
                    child, draw_manager, parent=element, anim_offset=child_offset
                )

    def _set_auto_layer(self, element, layer):
        """
        Recursively set auto layer for elements without explicit layer.

        Args:
            element: Root element
            layer: Layer to assign
        """
        graphic_dict = getattr(element, "visual_dict", {})

        # Only set if not explicitly specified in config
        if "layer" not in graphic_dict:
            element.layer = layer

        # Recursively set for children
        if hasattr(element, "children"):
            for child in element.children:
                self._set_auto_layer(child, layer)

    def hide_all_screens(self):
        """Hide all active screens and clear modal stack."""
        # Hide all modals
        for screen_name in list(self.modal_stack):
            self._on_screen_hide(screen_name)
        self.modal_stack.clear()

        # Hide active screen
        if self.active_screen:
            self._on_screen_hide(self.active_screen)
            self.active_screen = None
