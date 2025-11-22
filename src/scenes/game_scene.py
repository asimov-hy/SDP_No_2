"""
game_scene.py
-------------
Main gameplay scene - runs active level with player, enemies, bullets.
"""

from src.scenes.base_scene import BaseScene
from src.systems.game_system_initializer import GameSystemInitializer
from src.core.runtime.game_settings import Debug
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState
from src.core.runtime.session_stats import update_session_stats
from src.core.services.event_manager import get_events, EnemyDiedEvent
from src.scenes.scene_state import SceneState


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

        # Load HUD
        self.ui.load_hud("hud/gameplay_hud.yaml")

        # Load game over overlay (hidden by default)
        self.ui.load_screen("game_over", "hud/game_over.yaml")

        # Reset game state
        self.game_over_shown = False
        update_session_stats().reset()

        # Start specific level if selected
        if self.selected_level_id:
            level_config = level_registry.get(self.selected_level_id)
            if level_config:
                DebugLogger.state(f"Starting level: {level_config.name}")
                self.level_manager.load(level_config.path)
                return

        # Otherwise start first level in campaign
        if self.campaign and len(self.campaign) > 0:
            first_level = self.campaign[0]
            DebugLogger.state(f"Starting level: {first_level.name}")
            self.level_manager.load(first_level.path)
        else:
            # Fallback to default start level
            start_level = level_registry.get_default_start()
            if start_level:
                DebugLogger.state(f"Starting level: {start_level.name}")
                self.level_manager.load(start_level.path)

    def on_exit(self):
        """Clean up when leaving gameplay."""
        # Clear HUD
        self.ui.clear_hud()

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

        # Track play time (only during active gameplay)
        update_session_stats().add_time(dt)

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

        # Debug overlays
        if Debug.HITBOX_VISIBLE:
            self.collision_manager.draw_debug(draw_manager)

    def handle_event(self, event):
        """Handle input events."""
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
        update_session_stats().add_kill()
        update_session_stats().add_score(10)  # Base score per kill

    def _show_game_over(self, victory: bool):
        """Show game over overlay with stats."""
        self.game_over_shown = True

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
            score_elem.text = f"Score: {update_session_stats().score}"
            score_elem.mark_dirty()

        kills_elem = self.ui.find_element_by_id("game_over", "kills_label")
        if kills_elem:
            kills_elem.text = f"Enemies Killed: {update_session_stats().enemies_killed}"
            kills_elem.mark_dirty()

        items_elem = self.ui.find_element_by_id("game_over", "items_label")
        if items_elem:
            items_elem.text = f"Items Collected: {update_session_stats().items_collected}"
            items_elem.mark_dirty()

        time_elem = self.ui.find_element_by_id("game_over", "time_label")
        if time_elem:
            minutes = int(update_session_stats().run_time // 60)
            seconds = int(update_session_stats().run_time % 60)
            time_elem.text = f"Time: {minutes}:{seconds:02d}"
            time_elem.mark_dirty()

        # Show overlay
        self.ui.show_screen("game_over", modal=True)

        DebugLogger.state(f"Game over shown (victory={victory})", category="game")
