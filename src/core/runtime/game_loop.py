"""
game_loop.py
------------
Defines the main GameLoop class responsible for orchestrating the entire
runtime cycle of the game.

Responsibilities
----------------
- Initialize pygame and global runtime systems (display, input, draw manager)
- Create and delegate control to the SceneManager
- Maintain the main timing loop (event → update → render)
- Maintain a global DebugHUD independent of scenes
"""

import pygame
import time

# Core runtime configurations
from src.core.runtime.game_settings import Display, Physics, Debug

# Core service managers
from src.core.services.input_manager import InputManager
from src.core.services.display_manager import DisplayManager
from src.core.services.scene_manager import SceneManager
from src.ui.core.ui_manager import UIManager

# Core debugging utilities
from src.core.debug.debug_logger import DebugLogger
from src.core.debug.debug_hud import DebugHUD

# Rendering system
from src.graphics.draw_manager import DrawManager


class GameLoop:
    """Core runtime controller that manages the game’s main loop."""

    def __init__(self):
        """Initialize pygame and all foundational systems."""
        DebugLogger.section("Initializing GameLoop")

        # -------------------------------------------------------
        # Initialize pygame systems
        # -------------------------------------------------------
        pygame.init()
        pygame.font.init()

        # -------------------------------------------------------
        # Window Setup
        # -------------------------------------------------------
        self._set_icon()
        pygame.display.set_caption(Display.CAPTION)
        DebugLogger.init_entry("Pygame")
        DebugLogger.init_sub("Configured Icon and Window Caption")

        # -------------------------------------------------------
        # Core Systems
        # -------------------------------------------------------
        self.display = DisplayManager(Display.WIDTH, Display.HEIGHT, Display.DEFAULT_WINDOW_SIZE)
        self.input_manager = InputManager()
        self.draw_manager = DrawManager()

        self.ui_manager = UIManager(
            self.display,
            self.draw_manager,
            game_width=Display.WIDTH,
            game_height=Display.HEIGHT
        )
        DebugLogger.init_sub("UIManager initialized")

        # -------------------------------------------------------
        # Global Debug HUD (independent of scenes)
        # -------------------------------------------------------
        self._last_perf_warn_time = 0

        self.debug_hud = DebugHUD(self.display, self.draw_manager)
        DebugLogger.init_sub("Bound [DisplayManager, DrawManager] dependencies", level=1)

        DebugLogger.init_entry("GameLoop Runtime")
        self.clock = pygame.time.Clock()
        DebugLogger.init_sub("Game Clock Initialized", level=1)
        self.running = True
        DebugLogger.init_sub("Runtime flag set True", level=1)

        # -------------------------------------------------------
        # Scene Management
        # -------------------------------------------------------
        self.scenes = SceneManager(
            self.display,
            self.input_manager,
            self.draw_manager,
            self.ui_manager
        )
        # DebugLogger.init_sub("Linked [SceneManager] to [DisplayManager], [InputManager], [DrawManager]", level=1)

    # ===========================================================
    # Core Runtime Loop
    # ===========================================================
    def run(self):
        """
        Main loop that runs until the game is closed.

        Responsibilities:
            - Update active scene and debug systems.
            - Render all visual elements each frame.
        """
        DebugLogger.section("Game Loop")

        fixed_dt = Physics.FIXED_DT
        accumulator = 0.0
        frame_count = 0

        while self.running:
            # ---------------------------------------------------
            # Frame timing (with safety clamp)
            # ---------------------------------------------------
            frame_time = self.clock.tick(Display.FPS) / 1000.0
            frame_time = min(frame_time, Physics.MAX_FRAME_TIME)
            accumulator += frame_time

            # ---------------------------------------------------
            # Handle all pending pygame events
            # ---------------------------------------------------
            self._handle_events()

            # ---------------------------------------------------
            # Fixed timestep update (physics, logic, input)
            # ---------------------------------------------------
            while accumulator >= fixed_dt:
                self.input_manager.update()
                self.scenes.update(fixed_dt)
                accumulator -= fixed_dt
                frame_count += 1

            # ---------------------------------------------------
            # Debug HUD and rendering pass
            # ---------------------------------------------------
            self.debug_hud.update(frame_time, pygame.mouse.get_pos())
            self._draw()

        # -------------------------------------------------------
        # Cleanup
        # -------------------------------------------------------
        pygame.quit()
        DebugLogger.system("Pygame terminated")

    # ===========================================================
    # Initialization Helpers
    # ===========================================================
    def _set_icon(self):
        """Attempt to load and apply the game window icon."""
        try:
            icon = pygame.image.load("assets/images/icons/202X_icon.png")
            pygame.display.set_icon(icon)
            # DebugLogger.state("Window icon set successfully")
        except FileNotFoundError:
            DebugLogger.warn("Missing icon image")

    # ===========================================================
    # Event Handling
    # ===========================================================
    def _handle_events(self):
        """
        Process pygame events and route them to components.

        Responsibilities:
            - Handle quit requests and window resizing.
            - Route all keyboard input (system-level and contextual)
              through InputManager.
            - Delegate ui and scene-specific input events.
        """
        events = pygame.event.get()
        for event in events:
            # ---------------------------------------------------
            # System-level quit event
            # ---------------------------------------------------
            if event.type == pygame.QUIT:
                self.running = False
                DebugLogger.action("Quit signal received")
                break

            # ---------------------------------------------------
            # Global / system-level input (always active)
            # Delegates to InputManager to handle F3, F11, etc.
            # ---------------------------------------------------
            self.input_manager.handle_system_input(event, self.display, self.debug_hud)

            # Scene handles event (may consume it via pause)
            if not self.scenes.handle_event(event):  # Returns True if consumed
                self.debug_hud.handle_event(event)

    # ===========================================================
    # Rendering Pipeline (with profiling)
    # ===========================================================
    def _draw(self):
        """
        Draw everything managed by the active scene and debug HUD.
        Includes basic profiling for each rendering stage.
        """
        start_total = time.perf_counter()

        game_surface = self.display.get_game_surface()
        self.draw_manager.clear()

        # -------------------------------------------------------
        # Profile: Scene Draw
        # -------------------------------------------------------
        t_scene = time.perf_counter()
        self.scenes.draw(self.draw_manager)
        scene_time = (time.perf_counter() - t_scene) * 1000

        # -------------------------------------------------------
        # Profile: Debug HUD Draw
        # -------------------------------------------------------
        t_hud = time.perf_counter()
        player = self.scenes.get_player()

        self.debug_hud.draw(self.draw_manager, player)
        hud_time = (time.perf_counter() - t_hud) * 1000

        # -------------------------------------------------------
        # Profile: Render to Display
        # -------------------------------------------------------
        t_render = time.perf_counter()
        self.draw_manager.render(game_surface, debug=Debug.HITBOX_VISIBLE)
        self.display.render()
        render_time = (time.perf_counter() - t_render) * 1000

        # -------------------------------------------------------
        # Frame Summary
        # -------------------------------------------------------
        # Frame Summary
        frame_time_ms = (time.perf_counter() - start_total) * 1000

        fps = 1000.0 / frame_time_ms if frame_time_ms > 0 else 0.0

        # Delegate all metrics tracking to DebugHUD
        self.debug_hud.record_frame_metrics(frame_time_ms, scene_time, render_time, fps)

        # Slow frame warning (stays in GameLoop - it's a runtime concern)
        if frame_time_ms > Debug.FRAME_TIME_WARNING:
            now = time.perf_counter()
            if now - self._last_perf_warn_time > 1.0:  # Throttle to 1/sec
                self._last_perf_warn_time = now
                DebugLogger.warn(
                    f"Perf ⚠️ SLOW FRAME: {frame_time_ms:.2f} ms "
                    f"(Scene={scene_time:.2f} | HUD={hud_time:.2f} | Render={render_time:.2f})"
                )
