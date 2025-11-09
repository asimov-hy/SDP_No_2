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

from src.core.game_settings import Display, Physics, Debug

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
        DebugLogger.init("Begin GameLoop Initialization")

        # -------------------------------------------------------
        # Initialize pygame systems
        # -------------------------------------------------------
        pygame.init()
        pygame.font.init()

        DebugLogger.init("╔" + "═" * 64 + "╗", show_meta=False)
        DebugLogger.init("║{:^64}║".format("INITIALIZING GAMELOOP"), show_meta=False)
        DebugLogger.init("╠" + "═" * 64 + "╣", show_meta=False)
        # DebugLogger.init"║{:^64}║".format())

        # -------------------------------------------------------
        # Window Setup
        # -------------------------------------------------------
        self._set_icon()
        pygame.display.set_caption(Display.CAPTION)
        DebugLogger.init("║{:<56}║".format(f"\t[GameLoop][INIT]\t\t→  Icon Set. Caption Set."), show_meta=False)
        DebugLogger.init("║" + " " * 64 + "║", show_meta=False)

        # -------------------------------------------------------
        # Engine Core Systems
        # -------------------------------------------------------

        DebugLogger.init("╠────────────────────── ENGINE CORE SYSTEMS ─────────────────────╣", show_meta=False)
        self.display = DisplayManager(Display.WIDTH, Display.HEIGHT)
        self.input = InputManager()
        self.draw_manager = DrawManager()
        self.clock = pygame.time.Clock()
        self.running = True
        DebugLogger.init("║" + " " * 64 + "║", show_meta=False)

        # -------------------------------------------------------
        # Scene Management
        # -------------------------------------------------------

        DebugLogger.init("╠─────────────────── SCENE MANAGEMENT SYSTEMS ───────────────────╣", show_meta=False)
        self.scenes = SceneManager(self.display, self.input,self.draw_manager)
        DebugLogger.init("║" + " " * 64 + "║", show_meta=False)

        # -------------------------------------------------------
        # Global Debug HUD (independent of scenes)
        # -------------------------------------------------------
        DebugLogger.init("╠─────────────────────────── DEBUG HUD ──────────────────────────╣", show_meta=False)
        self.debug_hud = DebugHUD(self.display)
        self.debug_hud.draw_manager = self.draw_manager
        DebugLogger.init("║" + " " * 64 + "║", show_meta=False)
        DebugLogger.init("╚" + "═" * 64 + "╝", show_meta=False)

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
        DebugLogger.action("Entering main loop")

        fixed_dt = Physics.FIXED_DT
        accumulator = 0.0
        frame_count = 0

        while self.running:
            frame_time = self.clock.tick() / 1000.0
            frame_time = min(frame_time, Physics.MAX_FRAME_TIME)
            accumulator += frame_time

            self._handle_events()

            while accumulator >= fixed_dt:
                self.input.update()
                self.scenes.update(fixed_dt)

                accumulator -= fixed_dt
                frame_count += 1

            self.debug_hud.update(pygame.mouse.get_pos())

            self._draw()

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
                DebugLogger.action("Quit signal received")
                break

            # Global keyboard shortcuts
            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F11:
                    self.display.toggle_fullscreen()

                elif event.key == pygame.K_F3:
                    self.debug_hud.toggle()

                    # Sync hitbox rendering with HUD visibility
                    Debug.HITBOX_VISIBLE = self.debug_hud.visible
                    state = "Visible" if Debug.HITBOX_VISIBLE else "Hidden"
                    DebugLogger.action(
                        f"Hitbox rendering set → {state} (HUD={'Shown' if self.debug_hud.visible else 'Hidden'})")

            # Window resizing
            if event.type == pygame.VIDEORESIZE:
                self.display.handle_resize(event)

            # Scene-specific and global UI events
            self.scenes.handle_event(event)
            self.debug_hud.handle_event(event)

    # ===========================================================
    # Rendering Pipeline (with profiling)
    # ===========================================================
    def _draw(self):
        """Draw everything managed by the active scene, with per-stage profiling."""
        import time
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
        self.debug_hud.draw(self.draw_manager)
        hud_time = (time.perf_counter() - t_hud) * 1000

        # -------------------------------------------------------
        # Profile: Render to Display
        # -------------------------------------------------------
        t_render = time.perf_counter()
        self.draw_manager.render(game_surface)
        self.display.render()
        render_time = (time.perf_counter() - t_render) * 1000

        # -------------------------------------------------------
        # Frame Summary
        # -------------------------------------------------------
        frame_time_ms = (time.perf_counter() - start_total) * 1000

        if frame_time_ms > Debug.FRAME_TIME_WARNING:
            DebugLogger.warn(
                f"Perf ⚠️ SLOW FRAME: {frame_time_ms:.2f} ms (Scene={scene_time:.2f} | HUD={hud_time:.2f} | Render={render_time:.2f})"
            )
