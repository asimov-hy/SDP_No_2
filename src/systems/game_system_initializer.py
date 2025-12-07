"""
game_system_initializer.py
---------------------------
System initialization for GameScene.
Extracts all setup logic from GameScene.__init__ into reusable initializer.
"""

from src.systems.system_initializer import SystemInitializer
from src.core.runtime.game_settings import Display
from src.core.debug.debug_logger import DebugLogger

# Entity and system imports
from src.entities.player.player_core import Player

from src.systems.entity_management.bullet_manager import BulletManager
from src.systems.entity_management.spawn_manager import SpawnManager
from src.systems.entity_management.item_manager import ItemManager
from src.systems.entity_management.entity_registry import EntityRegistry

from src.systems.collision.collision_manager import CollisionManager

from src.systems.level.level_manager import LevelManager
from src.systems.level.stage_loader import StageLoader
from src.systems.level.wave_scheduler import WaveScheduler

from src.systems.effects.effects_manager import EffectsManager
from src.systems.entity_management.hazard_manager import HazardManager

# Animation auto-register imports
from src.graphics.animations.entities_animation import player_animation  # noqa: F401
from src.graphics.animations.entities_animation import enemy_animation  # noqa: F401
from src.graphics.animations.animation_effects import common_animation  # noqa: F401

from src.ui.core.ui_manager import UIManager

# Auto-discover all entity classes for registration
EntityRegistry.discover_entities(
    "src.entities.enemies",
    "src.entities.bullets",
    "src.entities.items",
    "src.entities.bosses",
    "src.entities.environments",
)


class GameSystemInitializer(SystemInitializer):
    """
    Initializes all systems required for gameplay.
    Replaces GameScene's 6 private init methods.
    """

    def initialize(self) -> dict:
        """
        Initialize gameplay systems in dependency order.

        Returns:
            dict: All initialized systems
        """
        DebugLogger.init_entry("Initializing Game Systems")

        systems = {}

        # Initialize systems in dependency order
        systems["ui"] = self._init_ui()
        systems["player"] = self._init_player()

        # Combat systems (depend on player)
        combat_systems = self._init_combat(systems["player"])
        systems.update(combat_systems)

        # Spawning systems (depend on collision)
        spawn_systems = self._init_spawning(systems["collision_manager"])
        systems.update(spawn_systems)

        # Link managers to player for shield system
        systems["player"]._collision_manager = systems["collision_manager"]
        systems["player"]._spawn_manager = systems["spawn_manager"]

        # Level system (depends on spawn + player)
        systems["level_manager"] = self._init_level_system(
            systems["spawn_manager"],
            systems["player"],
            systems["bullet_manager"],
            systems["hazard_manager"],
        )

        DebugLogger.init_entry("Game Systems Initialized")
        return systems

    # ===========================================================
    # System Initialization Methods
    # ===========================================================
    def _init_ui(self) -> UIManager:
        """Initialize UI system."""
        ui = self.services.ui_manager  # Use existing
        ui.load_screen("pause", "screens/pause_screen.yaml")
        return ui

    def _init_player(self) -> Player:
        """Initialize player entity."""
        start_x = Display.WIDTH / 2
        start_y = Display.HEIGHT / 2

        player = Player(
            x=start_x,
            y=start_y,
            draw_manager=self.draw_manager,
            input_manager=self.input_manager,
        )

        # Register player for cross-system access
        self.services.register_entity("player", player)

        return player

    def _init_combat(self, player) -> dict:
        """
        Initialize bullet and collision systems.

        Args:
            player: Player instance

        Returns:
            dict: {"bullet_manager": ..., "collision_manager": ...}
        """
        bullet_manager = BulletManager(draw_manager=self.draw_manager)
        player.bullet_manager = bullet_manager
        DebugLogger.init_sub("Connected [Player] → [BulletManager]")

        bullet_manager.register_bullet_config("player", player.get_bullet_config())

        bullet_manager.prewarm_pool(
            owner="player",
            count=50,
        )

        # collision_manager = CollisionManager(
        #     player,
        #     bullet_manager,
        #     None
        # )
        #
        # bullet_manager.collision_manager = collision_manager
        collision_manager = CollisionManager(
            player,
            bullet_manager,
            None,  # spawn_manager not ready
        )
        bullet_manager.link_collision_manager(collision_manager)

        DebugLogger.init_sub("Bound [CollisionManager] to [BulletManager]")

        collision_manager.register_hitbox(player)
        DebugLogger.init_sub("Registered [Player] with [CollisionManager]")

        return {
            "bullet_manager": bullet_manager,
            "collision_manager": collision_manager,
        }

    def _init_spawning(self, collision_manager) -> dict:
        """
        Initialize spawn, item, and effects systems.

        Args:
            collision_manager: CollisionManager instance

        Returns:
            dict: {"spawn_manager": ..., "item_manager": ..., "effects_manager": ...}
        """
        spawn_manager = SpawnManager(self.draw_manager, self.display, collision_manager)

        collision_manager.spawn_manager = spawn_manager
        spawn_manager.enable_pooling("enemy", "straight", prewarm_count=10)

        item_manager = ItemManager(
            spawn_manager=spawn_manager, item_data_path="items.json"
        )
        DebugLogger.init_sub("Connected [ItemManager] → [SpawnManager]")

        effects_manager = EffectsManager(spawn_manager)
        DebugLogger.init_sub("Connected [EffectsManager] → [SpawnManager]")

        hazard_manager = HazardManager(
            self.draw_manager, collision_manager, spawn_manager=spawn_manager
        )
        DebugLogger.init_sub("Initialized [HazardManager]")

        return {
            "spawn_manager": spawn_manager,
            "item_manager": item_manager,
            "effects_manager": effects_manager,
            "hazard_manager": hazard_manager,
        }

    def _init_level_system(
        self, spawn_manager, player, bullet_manager, hazard_manager
    ) -> LevelManager:
        """
        Initialize level management with dependency injection.

        Args:
            spawn_manager: SpawnManager instance
            player: Player instance
            bullet_manager: BulletManager instance

        Returns:
            LevelManager instance
        """
        stage_loader = StageLoader(spawn_manager)
        wave_scheduler = WaveScheduler(
            spawn_manager, player, bullet_manager, hazard_manager
        )
        return LevelManager(stage_loader, wave_scheduler)
