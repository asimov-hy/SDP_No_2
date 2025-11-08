"""
ui_manager.py
-------------
Central controller for all UI elements and UI subsystems.

Responsibilities
----------------
- Create and store UI elements (buttons, bars, etc.).
- Manage logical UI groups (HUD, menus, system overlays).
- Update element states each frame (hover detection, animation).
- Handle mouse click actions.
- Delegate rendering requests to the DrawManager.
- Attach specialized UI subsystems like HUDManager or DebugHUD.
"""

import pygame
from src.core.settings import Display
from src.ui.button import Button
from src.core.utils.debug_logger import DebugLogger

class UIManager:
    """Manages all UI elements: creation, updates, input, and rendering."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, display_manager, draw_manager):
        """
        Initialize UIManager with access to display and draw systems.

        Args:
            display_manager: Provides resolution and coordinate handling.
            draw_manager: Handles UI rendering and icon resources.
        """
        self.display_manager = display_manager
        self.draw_manager = draw_manager

        # Organized groups for scalability
        self.groups = {
            "hud": [],       # In-game overlays (health bar, ammo, etc.)
            "menus": [],     # Interactive menus (pause, settings, etc.)
            "system": []     # Popups, fade overlays, notifications
        }

        # Active group determines who receives input
        self.active_group = "hud"

        # Subsystem registry (HUDManager, DebugHUD, etc.)
        self.subsystems = {}

        # Initialize base developer UI
        self._create_base_ui()
        # DebugLogger.system("Initialized with default groups and subsystems")

    # ===========================================================
    # Initialization Helpers
    # ===========================================================
    def _create_base_ui(self):
        """Initialize developer/debug UI elements (optional for builds)."""
        pass

    # ===========================================================
    # Group Management
    # ===========================================================
    def register(self, element, group="hud"):
        """Add a UI element to the specified group."""
        self.groups.setdefault(group, []).append(element)

        # Auto-inject DrawManager for consistent icon rendering
        if hasattr(element, "draw_manager"):
            element.draw_manager = self.draw_manager

        # DebugLogger.action(f"Registered element in group '{group}'")

    def remove(self, element, group=None):
        """Remove a UI element from its group or all groups."""
        if group:
            if element in self.groups.get(group, []):
                self.groups[group].remove(element)
        else:
            for g in self.groups.values():
                if element in g:
                    g.remove(element)
        # DebugLogger.state(f"Removed element from '{group or 'all'}'")

    def set_active_group(self, group_name):
        """Switch which group receives input (e.g., 'menus', 'hud')."""
        if group_name in self.groups:
            self.active_group = group_name
            # DebugLogger.state(f"Active group changed → {group_name}")
        else:
            DebugLogger.warn(f"Tried to activate unknown group '{group_name}'")
            pass

    # ===========================================================
    # Subsystem Integration
    # ===========================================================
    def attach_subsystem(self, name, subsystem):
        """
        Attach a specialized UI subsystem (HUDManager, MenuManager, etc.).

        Subsystems must implement:
            - update(mouse_pos)
            - draw(draw_manager)
            - handle_event(event)
        """
        self.subsystems[name] = subsystem

        # Inject DrawManager if supported
        if hasattr(subsystem, "draw_manager"):
            subsystem.draw_manager = self.draw_manager

        # DebugLogger.system(f"Attached subsystem '{name}'")

    # ===========================================================
    # Frame Updates
    # ===========================================================
    def update(self, mouse_pos):
        """Update all visible elements in the active group and subsystems."""
        # Update standalone elements in current active group
        for elem in self.groups[self.active_group]:
            if elem.visible:
                elem.update(mouse_pos)

        # Update attached sub-managers (HUDs, menus, debug)
        for subsystem in self.subsystems.values():
            subsystem.update(mouse_pos)

        # DebugLogger.state(f"Updated group '{self.active_group}' and subsystems")

    # ===========================================================
    # Input Handling
    # ===========================================================
    def handle_event(self, event):
        """
        Route input events to UI elements and subsystems.

        Returns:
            str | None: Action string (e.g., 'pause', 'quit') if triggered.
        """
        # Route to subsystems first (so menus/debug can intercept)
        for subsystem in self.subsystems.values():
            action = subsystem.handle_event(event)
            if action:
                # DebugLogger.action(f"Subsystem action triggered: {action}")
                return action

        # Then route to active group
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for elem in self.groups[self.active_group]:
                if elem.visible and elem.enabled:
                    action = elem.handle_click(event.pos)
                    if action:
                        # DebugLogger.action(f"Element triggered action: {action}")
                        return action
        return None

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """Render all active UI elements and visible subsystems."""
        # Draw subsystems (HUDs, debug overlays)
        for subsystem in self.subsystems.values():
            subsystem.draw(draw_manager)

        # Draw group-level elements
        for elem in self.groups[self.active_group]:
            if elem.visible:
                draw_manager.queue_draw(elem.render_surface(), elem.rect, elem.layer)

    # DebugLogger.state(f"Drew UI group '{self.active_group}' and subsystems")