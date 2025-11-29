"""
main_loop.py
------------
Core game loop orchestrating timing, events, updates, and rendering.

Responsibilities:
- Initialize pygame and core systems
- Maintain fixed timestep update loop
- Coordinate event handling, updates, and rendering
- Manage global debug HUD
"""

import pygame
import time

from src.core.runtime.game_settings import Display, Physics, Debug
from src.core.services.input_manager import InputManager
from src.core.services.display_manager import DisplayManager
from src.core.services.scene_manager import SceneManager
from src.ui.core.ui_manager import UIManager
from src.core.debug.debug_logger import DebugLogger
from src.core.debug.debug_hud import DebugHUD
from src.graphics.draw_manager import DrawManager


class MainLoop:
    """
    Core runtime controller managing the game's main loop.

    Implements a fixed timestep for physics/logic with variable rendering.
    """

    # ===========================================================
    # Initialization
    # ===========================================================

    def __init__(self):
        """Initialize pygame and all core systems."""
        DebugLogger.section("Initializing MainLoop")

        self._init_pygame()
        self._init_core_systems()
        self._init_debug_systems()
        self._init_scene_manager()

    def _init_pygame(self):
        """Initialize pygame subsystems and window."""
        pygame.init()
        pygame.font.init()

        self._set_window_icon()
        pygame.display.set_caption(Display.CAPTION)

        DebugLogger.init_entry("Pygame")
        DebugLogger.init_sub("Configured Icon and Window Caption")

    def _init_core_systems(self):
        """Initialize display, input, drawing, and UI systems."""
        self.display = DisplayManager(
            Display.WIDTH,
            Display.HEIGHT,
            Display.DEFAULT_WINDOW_SIZE
        )
        self.input_manager = InputManager(display_manager=self.display)
        self.draw_manager = DrawManager()

        self.ui_manager = UIManager(
            self.display,
            self.draw_manager,
            input_manager=self.input_manager,
            game_width=Display.WIDTH,
            game_height=Display.HEIGHT
        )
        DebugLogger.init_sub("UIManager initialized")

    def _init_debug_systems(self):
        """Initialize debug HUD and performance tracking."""
        self.debug_hud = DebugHUD(self.display, self.draw_manager)
        self._last_perf_warn_time = 0.0

        DebugLogger.init_sub("Bound [DisplayManager, DrawManager] dependencies", level=1)

    def _init_scene_manager(self):
        """Initialize scene management and runtime state."""
        self.scenes = SceneManager(
            self.display,
            self.input_manager,
            self.draw_manager,
            self.ui_manager
        )

        self.clock = pygame.time.Clock()
        self.running = True

        DebugLogger.init_entry("Main Loop Runtime")
        DebugLogger.init_sub("Game Clock Initialized", level=1)
        DebugLogger.init_sub("Runtime flag set True", level=1)

    def _set_window_icon(self):
        """Load and apply window icon."""
        try:
            icon = pygame.image.load("assets/images/icons/202X_icon.png")
            pygame.display.set_icon(icon)
        except FileNotFoundError:
            DebugLogger.warn("Missing icon image")

    # ===========================================================
    # Main Loop
    # ===========================================================

    def run(self):
        """
        Execute main game loop until quit.

        Uses fixed timestep for updates with accumulator pattern.
        Rendering happens once per frame after all updates.
        """
        DebugLogger.section("Game Loop")

        fixed_dt = Physics.FIXED_DT
        accumulator = 0.0

        while self.running:
            # Frame timing with safety clamp
            frame_time = self.clock.tick(Display.FPS) / 1000.0
            frame_time = min(frame_time, Physics.MAX_FRAME_TIME)
            accumulator += frame_time

            # Process events
            self._handle_events()

            # Fixed timestep updates
            while accumulator >= fixed_dt:
                self.input_manager.update()
                self.scenes.update(fixed_dt)
                accumulator -= fixed_dt

            # Render
            self._draw(frame_time)

        # Cleanup
        pygame.quit()
        DebugLogger.system("Pygame terminated")

    # ===========================================================
    # Event Handling
    # ===========================================================

    def _handle_events(self):
        """
        Process all pending pygame events.

        Routes events to:
        1. Quit handling
        2. System input (F3, F11)
        3. Scene-specific handling
        4. Debug HUD
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                DebugLogger.action("Quit signal received")
                break

            # Global hotkeys (always active)
            self.input_manager.handle_system_input(
                event, self.display, self.debug_hud
            )

            # Scene handles event, falls through to debug HUD if not consumed
            if not self.scenes.handle_event(event):
                self.debug_hud.handle_event(event)

    # ===========================================================
    # Rendering
    # ===========================================================

    def _draw(self, frame_time: float):
        """
        Execute rendering pipeline.

        Args:
            frame_time: Time since last frame (for debug HUD update)
        """
        game_surface = self.display.get_game_surface()
        self.draw_manager.clear()

        # Profile and render based on debug state
        if Debug.PROFILING_ENABLED or Debug.HITBOX_VISIBLE:
            self._draw_with_profiling(frame_time)
        else:
            self._draw_simple(frame_time)

    def _draw_simple(self, frame_time: float):
        """Fast path rendering without profiling overhead."""
        game_surface = self.display.get_game_surface()

        # Update debug HUD (tracks metrics even when hidden)
        self.debug_hud.update(frame_time, pygame.mouse.get_pos())

        # Scene rendering
        self.scenes.draw(self.draw_manager)

        # Debug HUD (only draws if visible)
        self.debug_hud.draw(self.draw_manager, player=None)

        # Final render
        self.draw_manager.render(game_surface, debug=False)
        self.display.render()

        # Record basic metrics (FPS only)
        fps = self.clock.get_fps()
        self.debug_hud.record_frame_metrics(0.0, 0.0, 0.0, fps)

    def _draw_with_profiling(self, frame_time: float):
        """Debug path with full performance profiling."""
        start_total = time.perf_counter()

        # Update debug HUD
        self.debug_hud.update(frame_time, pygame.mouse.get_pos())

        # Profile: Scene Draw
        t_scene = time.perf_counter()
        self.scenes.draw(self.draw_manager)
        scene_time = (time.perf_counter() - t_scene) * 1000

        # Profile: Debug HUD Draw
        t_hud = time.perf_counter()
        player = self.scenes.get_player()
        self.debug_hud.draw(self.draw_manager, player)
        hud_time = (time.perf_counter() - t_hud) * 1000

        # Profile: Render to Display
        t_render = time.perf_counter()
        game_surface = self.display.get_game_surface()
        self.draw_manager.render(game_surface, debug=True)
        self.display.render()
        render_time = (time.perf_counter() - t_render) * 1000

        # Record metrics
        frame_time_ms = (time.perf_counter() - start_total) * 1000
        fps = self.clock.get_fps()
        self.debug_hud.record_frame_metrics(frame_time_ms, scene_time, render_time, fps)

        # Slow frame warning (throttled)
        self._check_slow_frame(frame_time_ms, scene_time, hud_time, render_time)

    def _check_slow_frame(self, frame_time_ms: float, scene_time: float,
                          hud_time: float, render_time: float):
        """Log warning for slow frames (throttled to 1/second)."""
        if frame_time_ms <= Debug.FRAME_TIME_WARNING:
            return

        now = time.perf_counter()
        if now - self._last_perf_warn_time > 1.0:
            self._last_perf_warn_time = now
            DebugLogger.warn(
                f"Perf ⚠ SLOW FRAME: {frame_time_ms:.2f}ms "
                f"(Scene={scene_time:.2f} | HUD={hud_time:.2f} | Render={render_time:.2f})"
            )