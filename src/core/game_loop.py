"""
game_loop.py
------------
Defines the main GameLoop class responsible for orchestrating the entire
runtime cycle of the game.

Responsibilities
----------------
- Initialize pygame and global engine systems (display, input, draw manager)
- Create and delegate control to the SceneManager
- Maintain the main timing loop (event → update → render)
- Maintain a global DebugHUD independent of scenes
"""

import pygame

from src.core.settings import *

from src.core.engine.input_manager import InputManager
from src.core.engine.display_manager import DisplayManager
from src.core.engine.scene_manager import SceneManager

from src.core.utils.debug_logger import DebugLogger

from src.graphics.draw_manager import DrawManager

from src.ui.subsystems.debug_hud import DebugHUD

class GameLoop:
    """Core runtime controller that manages the game’s main loop."""

    def __init__(self):
        """Initialize pygame and all foundational systems."""
        pygame.display.set_caption("202X")

        # -------------------------------------------------------
        # Engine Core Systems
        # -------------------------------------------------------
        self.display = DisplayManager(GAME_WIDTH, GAME_HEIGHT)
        self.input = InputManager()
        self.draw_manager = DrawManager()
        self.clock = pygame.time.Clock()
        self.running = True
        DebugLogger.system("GameLoop", "Core systems initialized")

        # -------------------------------------------------------
        # Scene Management
        # -------------------------------------------------------
        self.scenes = SceneManager(
            self.display,
            self.input,
            self.draw_manager
        )
        DebugLogger.system("GameLoop", "SceneManager initialized")

        # -------------------------------------------------------
        # Global Debug HUD (independent of scenes)
        # -------------------------------------------------------
        self.debug_hud = DebugHUD(self.display)
        self.debug_hud.draw_manager = self.draw_manager

        # -------------------------------------------------------
        # Window Setup
        # -------------------------------------------------------
        self._set_icon()

    # ===========================================================
    # Core Runtime Loop
    # ===========================================================
    def run(self):
        """
        Main loop that runs until the game is closed.

        Responsibilities:
            - Process input events.
            - Update active scene and debug systems.
            - Render all visual elements each frame.
        """
        DebugLogger.action("GameLoop", "Entering main loop")

        while self.running:
            dt = self.clock.tick(FPS) / 1000  # Delta time (seconds)
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

        DebugLogger.system("GameLoop", "Pygame terminated")

    # ===========================================================
    # Initialization Helpers
    # ===========================================================
    def _set_icon(self):
        """Attempt to load and apply the game window icon."""
        try:
            icon = pygame.image.load("assets/images/icons/202X_icon.png")
            pygame.display.set_icon(icon)
            DebugLogger.state("GameLoop", "Window icon set successfully")
        except FileNotFoundError:
            DebugLogger.warn("GameLoop", "Missing icon image")

    # ===========================================================
    # Event Handling
    # ===========================================================
    def _handle_events(self):
        """
        Process pygame events and route them to subsystems.

        Responsibilities:
            - Handle quit requests and window resizing.
            - Manage global hotkeys (F3 for debug, F11 for fullscreen).
            - Delegate input events to SceneManager and DebugHUD.
        """
        for event in pygame.event.get():
            # System-level quit event
            if event.type == pygame.QUIT:
                self.running = False
                DebugLogger.action("GameLoop", "Quit signal received")
                return

            # Global keyboard shortcuts
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F11:
                    self.display.toggle_fullscreen()
                    state = "ON" if getattr(self.display, "is_fullscreen", False) else "OFF"

                elif event.key == pygame.K_F3:
                    self.debug_hud.toggle()


            # Window resizing
            if event.type == pygame.VIDEORESIZE:
                self.display.handle_resize(event)

            # Scene-specific and global UI events
            self.scenes.handle_event(event)
            self.debug_hud.handle_event(event)

    # ===========================================================
    # Update Logic
    # ===========================================================
    def _update(self, dt: float):
        """
        Update all core systems.

        Args:
            dt (float): Delta time (seconds) since last frame.
        """
        self.input.update()
        self.scenes.update(dt)
        self.debug_hud.update(pygame.mouse.get_pos())

    # ===========================================================
    # Rendering Pipeline
    # ===========================================================
    def _draw(self):
        """Draw everything managed by the active scene."""
        game_surface = self.display.get_game_surface()
        self.draw_manager.clear()

        # Scene + UI drawing
        self.scenes.draw(self.draw_manager)
        self.debug_hud.draw(self.draw_manager)

        # Final render pass
        self.draw_manager.render(game_surface)
        self.display.render()
