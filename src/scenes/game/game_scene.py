"""
game_scene.py
-------------
Thin orchestrator that delegates to specialized controllers.
This file should remain around 50 lines - all logic goes in controllers.
"""

from src.core.runtime.gameplay_scene import GameplayScene
from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Display
from src.core.runtime.game_state import STATE

# Import all the setup code we need
from src.entities.player.player_core import Player
from src.ui.core.ui_manager import UIManager
from src.systems.combat.bullet_manager import BulletManager
from src.systems.collision.collision_manager import CollisionManager
from src.systems.level.spawn_manager import SpawnManager
from src.systems.level.level_manager import LevelManager
from src.systems.level.level_registry import LevelRegistry
from src.systems.items.item_manager import ItemManager

import src.graphics.animations.entities_animation.player_animation
import src.graphics.animations.entities_animation.enemy_animation

# Import controllers
from src.scenes.game.gameplay_controller import GameplayController
from src.scenes.game.entity_controller import EntityController
from src.scenes.game.level_controller import LevelController
from src.scenes.game.ui_controller import UIController


class GameScene(GameplayScene):
    """Thin orchestrator - delegates all logic to controllers."""

    def __init__(self, scene_manager):
        super().__init__(scene_manager)
        DebugLogger.section("Initializing Scene: GameScene")

        self.display = scene_manager.display
        self.input_manager = scene_manager.input_manager
        self.draw_manager = scene_manager.draw_manager

        # === SYSTEM INITIALIZATION (keep existing setup code) ===
        self._init_ui()
        self._init_player()
        self._init_combat()
        self._init_spawning()
        self._init_level_system()

        # === CREATE CONTROLLERS ===
        self.gameplay_ctrl = GameplayController(self)
        self.entity_ctrl = EntityController(self)
        self.level_ctrl = LevelController(self)
        self.ui_ctrl = UIController(self)

        DebugLogger.section("- Finished Initialization", only_title=True)
        DebugLogger.section("─" * 59 + "\n", only_title=True)

    def _init_ui(self):
        """Initialize UI system."""
        self.ui = UIManager(
            display_manager=self.display,
            draw_manager=self.draw_manager,
            game_width=Display.WIDTH,
            game_height=Display.HEIGHT
        )
        self.ui.load_screen("pause", "screens/pause_menu.yaml")

    def _init_player(self):
        """Initialize player entity."""
        start_x = Display.WIDTH / 2
        start_y = Display.HEIGHT / 2

        self.player = Player(
            x=start_x,
            y=start_y,
            draw_manager=self.draw_manager,
            input_manager=self.input_manager
        )

        # Register player globally for cross-system access
        STATE.register_entity("player", self.player)

        self.ui.register_binding("player", self.player)
        self.ui.load_hud("hud/player_hud.yaml")

    def _init_combat(self):
        """Initialize bullet and collision systems."""
        self.bullet_manager = BulletManager(draw_manager=self.draw_manager)
        self.player.bullet_manager = self.bullet_manager
        DebugLogger.init_sub("Connected [Player] → [BulletManager]")

        self.bullet_manager.prewarm_pool(
            owner="player",
            count=50,
            image=self.player.bullet_image
        )

        self.collision_manager = CollisionManager(
            self.player,
            self.bullet_manager,
            None
        )

        self.bullet_manager.collision_manager = self.collision_manager
        DebugLogger.init_sub("Bound [CollisionManager] to [BulletManager]")

        self.player.hitbox = self.collision_manager.register_hitbox(
            self.player,
            scale=self.player.hitbox_scale
        )
        DebugLogger.init_sub("Registered [Player] with [CollisionManager]")

    def _init_spawning(self):
        """Initialize spawn and item systems."""
        self.spawn_manager = SpawnManager(
            self.draw_manager,
            self.display,
            self.collision_manager
        )

        self.collision_manager.spawn_manager = self.spawn_manager
        self.spawn_manager.enable_pooling("enemy", "straight", prewarm_count=10)

        self.item_manager = ItemManager(
            spawn_manager=self.spawn_manager,
            item_data_path="items.json"
        )
        DebugLogger.init_sub("Connected [ItemManager] → [SpawnManager]")

    def _init_level_system(self):
        """Initialize level management."""
        self.level_manager = LevelManager(self.spawn_manager, player_ref=self.player)

        LevelRegistry.load_config("campaigns.json")
        self.campaign = LevelRegistry.get_campaign("test")

        if not self.campaign:
            DebugLogger.warn("Campaign 'test' not found or empty")
        else:
            DebugLogger.warn(f"Campaign loaded: {len(self.campaign)} levels")

        self.current_level_idx = 0

    # === DELEGATION TO CONTROLLERS ===

    def update(self, dt: float):
        """Delegate update to all controllers."""
        self.gameplay_ctrl.update(dt)
        self.entity_ctrl.update(dt)
        self.level_ctrl.update(dt)
        self.ui_ctrl.update(dt)

    def draw(self, draw_manager):
        """Delegate drawing to all controllers."""
        self.entity_ctrl.draw(draw_manager)
        self.gameplay_ctrl.draw(draw_manager)
        self.ui_ctrl.draw(draw_manager)

    def handle_event(self, event):
        """Delegate event handling to UI controller."""
        self.ui_ctrl.handle_event(event)

    def on_enter(self):
        """Delegate scene entry to level controller."""
        self.level_ctrl.on_enter()

    def on_pause(self):
        """Delegate pause to UI controller."""
        self.ui_ctrl.on_pause()

    def on_resume(self):
        """Delegate resume to UI controller."""
        self.ui_ctrl.on_resume()

    def get_pool_stats(self) -> dict:
        """Return pool statistics from spawn manager."""
        return self.spawn_manager.get_pool_stats()

    def on_exit(self):
        STATE.unregister_entity("player")
        DebugLogger.state("on_exit()")
