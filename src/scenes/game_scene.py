"""
game_scene.py
-------------
Main gameplay scene - runs active level with player, enemies, bullets.
"""

import copy
from src.scenes.base_scene import BaseScene
from src.systems.game_system_initializer import GameSystemInitializer
from src.core.runtime.game_settings import Debug
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState
from src.core.runtime.session_stats import get_session_stats
from src.core.services.event_manager import get_events, EnemyDiedEvent
from src.scenes.scene_state import SceneState
from src.ui.level_up_ui import LevelUpUI
from src.graphics.background_manager import DEFAULT_BACKGROUND_CONFIG

class GameScene(BaseScene):
    """Active gameplay scene."""

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "gameplay"

        # Initialize all game systems
        DebugLogger.section("Initializing GameScene")
        initializer = GameSystemInitializer(services)
        systems = initializer.initialize()

        # Store system references
        self.player = systems['player']
        self.player.sound_manager = services.get_global("sound_manager")
        self.collision_manager = systems['collision_manager']
        self.spawn_manager = systems['spawn_manager']
        self.bullet_manager = systems['bullet_manager']
        self.level_manager = systems['level_manager']
        self.ui = systems['ui']

        # Campaign tracking
        self.campaign = None
        self.current_level_idx = 0
        self.selected_level_id = None

        # Game over state
        self.game_over_shown = False

        # Set callbacks
        self.level_manager.on_level_complete = self._on_level_complete
        get_events().subscribe(EnemyDiedEvent, self._on_enemy_died_stats)

        # Initialize LevelUpUI
        self.level_up_ui = LevelUpUI(self.player)
        self.level_up_ui.on_close = lambda: self.input_manager.set_context("gameplay")
        self.last_player_level = self.player.level  # Track level changes

        DebugLogger.section("GameScene Initialized")

    def on_load(self, campaign_name=None, level_id=None, **scene_data):
        """Load campaign when scene is created."""
        # Store specific level to load
        self.selected_level_id = level_id

        # Load campaign from registry
        level_registry = self.services.get_global("level_registry")

        if campaign_name:
            self.campaign = level_registry.get_campaign(campaign_name)
            if self.campaign:
                DebugLogger.init_sub(f"Loaded campaign: {campaign_name} ({len(self.campaign)} levels)")
            else:
                DebugLogger.warn(f"Campaign '{campaign_name}' not found")
                self.campaign = []
        else:
            # Default campaign
            self.campaign = level_registry.get_campaign("test")
            if self.campaign:
                DebugLogger.init_sub(f"Loaded default campaign: test ({len(self.campaign)} levels)")
            else:
                self.campaign = []

    def on_enter(self):
        """Start first level when scene becomes active."""
        level_registry = self.services.get_global("level_registry")

        # Load BGM
        game_sound = self.services.get_global("sound_manager")
        game_sound.play_bgm("game_bgm", loop=-1)

        # Load HUD
        self.ui.load_hud("hud/player_hud.yaml")

        # Load game over overlay (hidden by default)
        self.ui.load_screen("game_over", "screens/game_over.yaml")

        # Reset game state
        self.game_over_shown = False
        get_session_stats().reset()

        # Start specific level if selected
        if self.selected_level_id:
            level_config = level_registry.get(self.selected_level_id)
            if level_config:
                DebugLogger.state(f"Starting level: {level_config.name}")
                self.level_manager.load(level_config.path)

                # Load background for this level
                level_data = self.level_manager.get_current_level_data()
                if level_data:
                    self._load_level_background(level_data)

                return

        # Otherwise start first level in campaign
        if self.campaign and len(self.campaign) > 0:
            first_level = self.campaign[0]
            DebugLogger.state(f"Starting level: {first_level.name}")
            self.level_manager.load(first_level.path)

            # Load background for this level
            level_data = self.level_manager.get_current_level_data()
            if level_data:
                self._load_level_background(level_data)

        else:
            # Fallback to default start level
            start_level = level_registry.get_default_start()
            if start_level:
                DebugLogger.state(f"Starting level: {start_level.name}")
                self.level_manager.load(start_level.path)

                # Load background for this level
                level_data = self.level_manager.get_current_level_data()
                if level_data:
                    self._load_level_background(level_data)

    def on_exit(self):
        """Clean up when leaving gameplay."""
        # Clear background
        self._clear_background()

        # Clear HUD
        self.ui.clear_hud()
        self.ui.hide_screen("game_over")

    def on_pause(self):
        """Show pause overlay."""
        self.ui.show_screen("pause", modal=True)

    def on_resume(self):
        """Hide pause overlay."""
        self.ui.hide_screen("pause")

    def update(self, dt: float):
        """Update all game systems."""
        # Check for player death
        if not self.game_over_shown and self.player.death_state == LifecycleState.DEAD:
            if self.level_up_ui.is_active:
                self.level_up_ui.hide()  # Force close level up UI
            self._show_game_over(victory=False)
            return

        # Don't update gameplay if game over is shown
        if self.game_over_shown:
            mouse_pos = self.input_manager.get_mouse_pos()
            self.ui.update(dt, mouse_pos)
            return

        # Don't update gameplay or track time if paused
        if self.state == SceneState.PAUSED:
            mouse_pos = self.input_manager.get_mouse_pos()
            self.ui.update(dt, mouse_pos)
            return

        if self.level_up_ui.is_active:
            # Switch to UI context for level up navigation
            if self.input_manager.context != "ui":
                self.input_manager.set_context("ui")

            self.level_up_ui.handle_input(self.input_manager)
            self.level_up_ui.update(dt)
            return

        # Check for level up BEFORE gameplay updates (single check with death guard)
        if self.player.level > self.last_player_level:
            if self.player.death_state == LifecycleState.ALIVE:
                DebugLogger.state(f"Level up! {self.last_player_level} -> {self.player.level}")
                self.input_manager.set_context("ui")  # Switch once when showing
                self.level_up_ui.show()
                self.last_player_level = self.player.level
                return
            else:
                # Player died while leveling - just update tracker, don't show UI
                self.last_player_level = self.player.level

        if self.input_manager.context != "gameplay":
            self.input_manager.set_context("gameplay")

        # Track play time (only during active gameplay)
        get_session_stats().add_time(dt)

        # Update scrolling background with player position for parallax
        player_pos = (self.player.virtual_pos.x, self.player.virtual_pos.y)
        self._update_background(dt, player_pos)

        # Core gameplay updates
        self.player.update(dt)
        self.spawn_manager.update(dt)
        self.bullet_manager.update(dt)
        self.level_manager.update(dt)

        # Collision detection
        self.collision_manager.update()
        self.collision_manager.detect()

        # Cleanup dead entities
        self.spawn_manager.cleanup()

        # UI update
        mouse_pos = self.input_manager.get_mouse_pos()
        self.ui.update(dt, mouse_pos)

    def draw(self, draw_manager):
        """Render all game elements."""
        # Entities
        self.player.draw(draw_manager)
        self.spawn_manager.draw()
        self.bullet_manager.draw(draw_manager)

        # UI/HUD
        self.ui.draw(draw_manager)

        self.level_up_ui.draw(draw_manager)

        # Debug overlays
        if Debug.HITBOX_VISIBLE:
            self.collision_manager.draw_debug(draw_manager)

    def handle_event(self, event):
        """Handle input events."""
        if self.level_up_ui.is_active:
            if self.level_up_ui.handle_event(event):
                return  # Event consumed by level up UI

        action = self.ui.handle_event(event)

        if action == "resume":
            self.scene_manager.resume_active_scene()
        elif action == "quit":
            self.scene_manager.set_scene("MainMenu")
        elif action == "return_to_menu":
            self.scene_manager.set_scene("MainMenu")

    def _on_level_complete(self):
        """Called when level is completed."""
        if not self.game_over_shown:
            self._show_game_over(victory=True)

    def _on_enemy_died_stats(self, event):
        """Track enemy kills in session stats."""
        get_session_stats().add_kill()
        get_session_stats().add_score(10)  # Base score per kill
        explosion_sound = self.services.get_global("sound_manager")
        explosion_sound.play_bfx("enemy_destroy")

    def _show_game_over(self, victory: bool):
        """Show game over overlay with stats."""
        self.game_over_shown = True
        end_sound = self.services.get_global("sound_manager")
        end_sound.play_bgm("game_over", -1)

        # Update title
        title_elem = self.ui.find_element_by_id("game_over", "title_label")
        if title_elem:
            if victory:
                title_elem.text = "MISSION ACCOMPLISHED"
                title_elem.text_color = (100, 255, 100)
            else:
                title_elem.text = "GAME OVER"
                title_elem.text_color = (255, 100, 100)
            title_elem.mark_dirty()

        # Update stats
        score_elem = self.ui.find_element_by_id("game_over", "score_label")
        if score_elem:
            score_elem.text = f"Score: {get_session_stats().score}"
            score_elem.mark_dirty()

        kills_elem = self.ui.find_element_by_id("game_over", "kills_label")
        if kills_elem:
            kills_elem.text = f"Enemies Killed: {get_session_stats().enemies_killed}"
            kills_elem.mark_dirty()

        items_elem = self.ui.find_element_by_id("game_over", "items_label")
        if items_elem:
            items_elem.text = f"Items Collected: {get_session_stats().items_collected}"
            items_elem.mark_dirty()

        time_elem = self.ui.find_element_by_id("game_over", "time_label")
        if time_elem:
            minutes = int(get_session_stats().run_time // 60)
            seconds = int(get_session_stats().run_time % 60)
            time_elem.text = f"Time: {minutes}:{seconds:02d}"
            time_elem.mark_dirty()

        # Show overlay
        self.ui.show_screen("game_over", modal=True)

        DebugLogger.state(f"Game over shown (victory={victory})", category="game")

    def _setup_background(self):
        """Initialize scrolling background from level config."""
        # Will be called after level loads
        pass

    def _load_level_background(self, level_config):
        """
        Load background from level configuration.

        Args:
            level_config: Level data dict with optional 'background' section
        """

        bg_config = copy.deepcopy(DEFAULT_BACKGROUND_CONFIG)

        # Merge level-specific overrides
        if "background" in level_config:
            level_bg = level_config["background"]

            # Merge layers
            if "layers" in level_bg:
                for i, layer_override in enumerate(level_bg["layers"]):
                    if i < len(bg_config["layers"]):
                        # Merge individual layer properties
                        bg_config["layers"][i].update(layer_override)
                    else:
                        # Add new layer
                        bg_config["layers"].append(layer_override)

        # Setup using base class method
        super()._setup_background(bg_config)
