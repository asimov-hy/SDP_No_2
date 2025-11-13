"""
game_scene.py
-------------
Defines the main in-game scene — includes core gameplay entities_animation
and the player HUD overlay.

Responsibilities
----------------
- Initialize gameplay entities_animation (e.g., Player).
- Update all active game logic each frame.
- Manage the in-game UI system (HUDManager, overlays).
- Forward input and events to appropriate subsystems.
"""

import pygame

# Core Systems
from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Debug

# Player Entity
from src.entities.player.player_core import Player

# UI Systems
from src.ui.ui_manager import UIManager
from src.ui.hud_manager import HUDManager

# Combat Systems
from src.systems.combat.bullet_manager import BulletManager
from src.systems.collision.collision_manager import CollisionManager

# Level and Spawn Systems
from src.systems.level.spawn_manager import SpawnManager
from src.systems.level.level_manager import LevelManager
from src.systems.level.pattern_registry import PatternRegistry


class GameScene:
    """Handles all gameplay entities_animation, logic, and UI systems."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, scene_manager):
        """
        Initialize the game scene, UI, and entities_animation.

        Args:
            scene_manager: Reference to SceneManager for access to display,
                           input, and draw subsystems.
        """
        DebugLogger.section("Initializing Scene: GameScene")

        self.scene_manager = scene_manager
        self.display = scene_manager.display
        self.input_manager = scene_manager.input_manager
        self.draw_manager = scene_manager.draw_manager

        # UI System Setup
        self.ui = UIManager(self.display, self.draw_manager)

        # Base HUD (game overlay)
        try:
            self.ui.attach_subsystem("hud", HUDManager())
        except Exception as e:
            DebugLogger.fail(f"HUDManager unavailable: {e}")

        # spawn player
        self.player = Player(draw_manager=self.draw_manager, input_manager=self.input_manager)

        # Bullet Manager Setup
        self.bullet_manager = BulletManager()

        self.player.bullet_manager = self.bullet_manager
        DebugLogger.init_sub("Connected [Player] → [BulletManager]")

        # Collision Manager Setup
        self.collision_manager = CollisionManager(
            self.player,
            self.bullet_manager,
            None
        )

        self.bullet_manager.collision_manager = self.collision_manager
        DebugLogger.init_sub("Bound [CollisionManager] to [BulletManager]")

        # Register player's hitbox through the CollisionManager
        self.player.hitbox = self.collision_manager.register_hitbox(
            self.player,
            scale=self.player.hitbox_scale
        )
        DebugLogger.init_sub("Registered [Player] with [CollisionManager]")
        DebugLogger.warn(f"Player hitbox owner ID: {id(self.player.hitbox.owner)}")

        # ===========================================================
        # Spawn Manager Setup
        # ===========================================================
        self.spawn_manager = SpawnManager(self.draw_manager, self.display, self.collision_manager)
        DebugLogger.warn(f"Player created. Is it in spawn_manager? {self.player in self.spawn_manager.entities}")

        self.collision_manager.spawn_manager = self.spawn_manager

        self.spawn_manager.enable_pooling("enemy", "straight", prewarm_count=10)

        # ===========================================================
        # Level Manager Setup
        # ===========================================================
        self.level_manager = LevelManager(self.spawn_manager)
        self.level_manager.on_stage_complete = self._on_stage_complete

        self.stage_queue = [
            "src/data/Stage 1.json",
            "src/data/Stage 2.json",
            "src/data/Stage 3.json"
        ]
        self.current_stage_idx = 0

        DebugLogger.section("- Finished Initialization", only_title=True)
        DebugLogger.section("─" * 59 + "\n", only_title=True)

        self.paused = False

    # ===========================================================
    # Event Handling
    # ===========================================================
    def handle_event(self, event):
        """
        Forward input and system events to UI and entities_animation.

        Args:
            event (pygame.event.Event): The event to process.
        """
        self.ui.handle_event(event)

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Update gameplay logic and UI each frame.

        Args:
            dt (float): Delta time (in seconds) since the last frame.
        """

        if self.paused:
            return

        # 1) Player Input & Update
        move = self.input_manager.get_normalized_move()
        self.player.move_vec = move

        # 2. Single entity pass (combines spawn + level logic)
        self.spawn_manager.update(dt)  # Updates entities_animation
        self.level_manager.update(dt)  # Only checks timers/waves

        # 3. Physics
        self.player.update(dt)

        # 4. Projectiles
        self.bullet_manager.update(dt)

        # 5. Collision
        self.collision_manager.update()
        self.collision_manager.detect()

        # 6. Cleanup
        self.spawn_manager.cleanup()

        # 7. UI
        self.ui.update(pygame.mouse.get_pos())

        # if not self.level_manager.active:  # when current stage finishes
        #     next_stage = self._get_next_stage()
        #     if next_stage:
        #         DebugLogger.state(f"Loading next stage: {next_stage}")
        #         self.level_manager.load(next_stage)
        #     else:
        #         DebugLogger.system("All stages complete — GameScene finished")

    def _on_stage_complete(self):
        """Callback fired by LevelManager when stage ends."""
        DebugLogger.system(f"Stage {self.current_stage_idx + 1} complete")

        self.spawn_manager.reset()

        # self.spawn_manager.cleanup()  # Clear all entities_animation
        self.current_stage_idx += 1

        if self.current_stage_idx < len(self.stage_queue):
            next_stage = self.stage_queue[self.current_stage_idx]
            DebugLogger.state(f"Loading: {next_stage}")
            self.level_manager.load(next_stage)
        else:
            DebugLogger.system("All stages complete")

    # ===========================================================
    # Rendering
    # ===========================================================
    def draw(self, draw_manager):
        """
        Render all entities_animation and UI elements to the draw queue.

        Args:
            draw_manager (DrawManager): Centralized renderer responsible for batching and displaying.
        """
        # Rendering Order (Layer Priority)
        self.spawn_manager.draw()
        self.bullet_manager.draw(draw_manager)
        self.player.draw(draw_manager)
        self.ui.draw(draw_manager)

        # Optional Debug Rendering
        if Debug.HITBOX_VISIBLE:
            self.collision_manager.draw_debug(draw_manager)

    # ===========================================================
    # Utilities
    # ===========================================================
    def get_pool_stats(self) -> dict:
        """Return current pool usage statistics."""
        stats = {}
        return self.spawn_manager.get_pool_stats()

    # ===========================================================
    # Lifecycle Hooks
    # ===========================================================
    def on_enter(self):
        DebugLogger.state("on_enter()")
        self.level_manager.load("levels/Stage 1.json")

    def on_exit(self):
        DebugLogger.state("on_exit()")

    def on_pause(self):
        self.paused = True
        self.level_manager.active = False
        DebugLogger.state("on_pause()")

    def on_resume(self):
        DebugLogger.state("on_resume()")

    def reset(self):
        DebugLogger.state("reset()")