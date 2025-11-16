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
from src.core.runtime.scene_manager import SceneManager

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
        self.display = DisplayManager(Display.WIDTH, Display.HEIGHT)
        self.input_manager = InputManager()
        self.draw_manager = DrawManager()

        # -------------------------------------------------------
        # Global Debug HUD (independent of scenes)
        # -------------------------------------------------------
        self.debug_hud = DebugHUD(self.display, self.draw_manager)
        DebugLogger.init_sub("Bound [DisplayManager] dependency", level=1)
        self.debug_hud.draw_manager = self.draw_manager
        DebugLogger.init_sub("Bound [DrawManager] dependency", level=1)

        DebugLogger.init_entry("GameLoop Runtime")
        self.clock = pygame.time.Clock()
        DebugLogger.init_sub("Game Clock Initialized", level=1)
        self.running = True
        DebugLogger.init_sub("Runtime flag set True", level=1)

        # -------------------------------------------------------
        # Scene Management
        # -------------------------------------------------------
        self.scenes = SceneManager(self.display, self.input_manager, self.draw_manager)
        # DebugLogger.init_sub("Linked [SceneManager] to [DisplayManager], [InputManager], [DrawManager]", level=1)

        # Dependency Injection: Link SceneManager back into InputManager
        self.input_manager.link_scene_manager(self.scenes)

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
            self.debug_hud.update(fixed_dt, pygame.mouse.get_pos())
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
            # Window resizing
            # ---------------------------------------------------
            if event.type == pygame.VIDEORESIZE:
                self.display.handle_resize(event)

            # ---------------------------------------------------
            # Global / system-level input (always active)
            # Delegates to InputManager to handle F3, F11, etc.
            # ---------------------------------------------------
            self.input_manager.handle_system_input(event, self.display, self.debug_hud)

            # ---------------------------------------------------
            # Scene-specific and debug HUD events
            # ---------------------------------------------------
            self.scenes.handle_event(event)
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
        player = None
        if hasattr(self.scenes, '_active_instance'):
            scene = self.scenes._active_instance
            if hasattr(scene, 'player'):
                player = scene.player

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

        # NEW: Timing breakdown for DebugHUD
        self.debug_hud.frame_time = frame_time_ms
        self.debug_hud.update_time = scene_time
        self.debug_hud.render_time = render_time

        # NEW: Store frame time history for graphing
        self.debug_hud.frame_time_history.append(frame_time_ms)
        if len(self.debug_hud.frame_time_history) > self.debug_hud.frame_time_history_max:
            self.debug_hud.frame_time_history.pop(0)

        # Add FPS to history (for graph)
        self.debug_hud.fps_history.append(fps)
        if len(self.debug_hud.fps_history) > self.debug_hud.fps_history_max:
            self.debug_hud.fps_history.pop(0)

        # Smoothed
        self.debug_hud.smoothed_fps = (
            self.debug_hud.smoothed_fps * 0.9 + fps * 0.1
            if self.debug_hud.smoothed_fps > 0 else fps
        )

        # Recent Average
        self.debug_hud.recent_fps_sum += fps
        self.debug_hud.recent_fps_count += 1

        if self.debug_hud.recent_fps_count > 300:  # 5-second window
            self.debug_hud.recent_fps_sum *= 0.5
            self.debug_hud.recent_fps_count = int(self.debug_hud.recent_fps_count * 0.5)

        # Max / Min tracking
        if fps > self.debug_hud.max_fps:
            self.debug_hud.max_fps = fps

        if fps < self.debug_hud.min_fps:
            self.debug_hud.min_fps = fps
            self.debug_hud.min_fps_time = time.strftime("%H:%M:%S")

        if frame_time_ms > Debug.FRAME_TIME_WARNING:
            DebugLogger.warn(
                f"Perf ⚠️ SLOW FRAME: {frame_time_ms:.2f} ms "
                f"(Scene={scene_time:.2f} | HUD={hud_time:.2f} | Render={render_time:.2f})"
            )
