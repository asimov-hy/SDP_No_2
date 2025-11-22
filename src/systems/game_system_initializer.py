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
from src.ui.core.ui_manager import UIManager
from src.systems.entity_management.bullet_manager import BulletManager
from src.systems.collision.collision_manager import CollisionManager
from src.systems.entity_management.spawn_manager import SpawnManager
from src.systems.level.level_manager import LevelManager
from src.systems.entity_management.item_manager import ItemManager

# game_system_initializer.py lines 22-24
# Animation modules imported for auto-registration side effects
from src.graphics.animations.entities_animation import player_animation  # noqa: F401
from src.graphics.animations.entities_animation import enemy_animation   # noqa: F401
from src.graphics.animations.animation_effects import common_animation   # noqa: F401


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
        systems['ui'] = self._init_ui()
        systems['player'] = self._init_player()

        # Combat systems (depend on player)
        combat_systems = self._init_combat(systems['player'])
        systems.update(combat_systems)

        # Spawning systems (depend on collision)
        spawn_systems = self._init_spawning(systems['collision_manager'])
        systems.update(spawn_systems)

        # Level system (depends on spawn + player)
        systems['level_manager'] = self._init_level_system(
            systems['spawn_manager'],
            systems['player']
        )

        DebugLogger.init_entry("Game Systems Initialized")
        return systems

    # ===========================================================
    # System Initialization Methods
    # ===========================================================
    def _init_ui(self) -> UIManager:
        """Initialize UI system."""
        ui = self.services.ui_manager  # Use existing
        ui.load_screen("pause", "hud/pause_hud.yaml")
        return ui

    def _init_player(self) -> Player:
        """Initialize player entity."""
        start_x = Display.WIDTH / 2
        start_y = Display.HEIGHT / 2

        player = Player(
            x=start_x,
            y=start_y,
            draw_manager=self.draw_manager,
            input_manager=self.input_manager
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

        bullet_manager.prewarm_pool(
            owner="player",
            count=50,
            image=player.bullet_image
        )

        collision_manager = CollisionManager(
            player,
            bullet_manager,
            None
        )

        bullet_manager.collision_manager = collision_manager
        DebugLogger.init_sub("Bound [CollisionManager] to [BulletManager]")

        collision_manager.register_hitbox(player)
        DebugLogger.init_sub("Registered [Player] with [CollisionManager]")

        return {
            "bullet_manager": bullet_manager,
            "collision_manager": collision_manager
        }

    def _init_spawning(self, collision_manager) -> dict:
        """
        Initialize spawn and item systems.

        Args:
            collision_manager: CollisionManager instance

        Returns:
            dict: {"spawn_manager": ..., "item_manager": ...}
        """
        spawn_manager = SpawnManager(
            self.draw_manager,
            self.display,
            collision_manager
        )

        collision_manager.spawn_manager = spawn_manager
        spawn_manager.enable_pooling("enemy", "straight", prewarm_count=10)

        item_manager = ItemManager(
            spawn_manager=spawn_manager,
            item_data_path="items.json"
        )
        DebugLogger.init_sub("Connected [ItemManager] → [SpawnManager]")

        return {
            "spawn_manager": spawn_manager,
            "item_manager": item_manager
        }

    def _init_level_system(self, spawn_manager, player) -> LevelManager:
        """
        Initialize level management.

        Args:
            spawn_manager: SpawnManager instance
            player: Player instance

        Returns:
            LevelManager instance
        """
        level_manager = LevelManager(spawn_manager, player_ref=player)
        return level_manager
