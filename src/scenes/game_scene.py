"""
game_scene.py
-------------
Main gameplay scene - runs active level with player, enemies, bullets.
"""

import pygame
import random
from src.scenes.base_scene import BaseScene
from src.systems.game_system_initializer import GameSystemInitializer
from src.core.runtime.game_settings import Debug
from src.systems.level.level_registry import LevelRegistry
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import LifecycleState
from src.core.runtime.session_stats import update_session_stats
from src.core.services.event_manager import get_events, EnemyDiedEvent, PlayerLevelUpEvent, PlayerSelectedUpgradeEvent
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
        
        # Level up selection state
        self.level_up_active = False
        self.available_upgrades = []  # Store the 3 randomly selected upgrades

        # Set callbacks
        self.level_manager.on_level_complete = self._on_level_complete
        get_events().subscribe(EnemyDiedEvent, self._on_enemy_died_stats)
        get_events().subscribe(PlayerLevelUpEvent, self._on_player_level_up)
        get_events().subscribe(PlayerSelectedUpgradeEvent, self._on_upgrade_selected)

        DebugLogger.section("GameScene Initialized")

    def on_load(self, campaign_name=None, level_id=None, **scene_data):
        """Load campaign when scene is created."""
        # Store specific level to load
        self.selected_level_id = level_id

        # Load campaign from registry
        if campaign_name:
            self.campaign = LevelRegistry.get_campaign(campaign_name)
            if self.campaign:
                DebugLogger.init_sub(f"Loaded campaign: {campaign_name} ({len(self.campaign)} levels)")
            else:
                DebugLogger.warn(f"Campaign '{campaign_name}' not found")
                self.campaign = []
        else:
            # Default campaign
            self.campaign = LevelRegistry.get_campaign("test")
            if self.campaign:
                DebugLogger.init_sub(f"Loaded default campaign: test ({len(self.campaign)} levels)")
            else:
                self.campaign = []

    def on_enter(self):
        """Start first level when scene becomes active."""
        # Load HUD
        self.ui.load_hud("hud/gameplay_hud.yaml")

        # Load game over overlay (hidden by default)
        self.ui.load_screen("game_over", "hud/game_over.yaml")
        
        # Load level up overlay (hidden by default)
        self.ui.load_screen("level_up", "screens/level_up.yaml")

        # Reset game state
        self.game_over_shown = False
        update_session_stats().reset()

        # Start specific level if selected
        if self.selected_level_id:
            level_config = LevelRegistry.get(self.selected_level_id)
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
            start_level = LevelRegistry.get_default_start()
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
            # Handle special case for level up (allow UI interactions but not gameplay)
            if self.level_up_active:
                mouse_pos = self.input_manager.get_mouse_pos()
                self.ui.update(dt, mouse_pos)
                return
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
        elif action in ("upgrade_1", "upgrade_2", "upgrade_3"):
            # Get index of selected upgrade (1, 2, or 3)
            idx = int(action.split("_")[1]) - 1
            if 0 <= idx < len(self.available_upgrades):
                self._select_upgrade(self.available_upgrades[idx])
        elif action in ("upgrade_health", "upgrade_damage", "upgrade_speed", "upgrade_firerate", "upgrade_multishot"):
            # Handle legacy actions for compatibility
            upgrade_type = action.split("_")[1]
            self._select_upgrade(upgrade_type)

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

        # Get overlay root element
        overlay = self.ui.screens.get("game_over")
        if not overlay:
            DebugLogger.warn("Game over overlay not loaded")
            return

        # Update title
        title_elem = self._find_element_by_id(overlay, "title_label")
        if title_elem:
            if victory:
                title_elem.text = "MISSION ACCOMPLISHED"
                title_elem.text_color = (100, 255, 100)
            else:
                title_elem.text = "GAME OVER"
                title_elem.text_color = (255, 100, 100)
            title_elem.mark_dirty()

        # Update stats
        score_elem = self._find_element_by_id(overlay, "score_label")
        if score_elem:
            score_elem.text = f"Score: {update_session_stats().score}"
            score_elem.mark_dirty()

        kills_elem = self._find_element_by_id(overlay, "kills_label")
        if kills_elem:
            kills_elem.text = f"Enemies Killed: {update_session_stats().enemies_killed}"
            kills_elem.mark_dirty()

        items_elem = self._find_element_by_id(overlay, "items_label")
        if items_elem:
            items_elem.text = f"Items Collected: {update_session_stats().items_collected}"
            items_elem.mark_dirty()

        time_elem = self._find_element_by_id(overlay, "time_label")
        if time_elem:
            minutes = int(update_session_stats().run_time // 60)
            seconds = int(update_session_stats().run_time % 60)
            time_elem.text = f"Time: {minutes}:{seconds:02d}"
            time_elem.mark_dirty()

        # Show overlay
        self.ui.show_screen("game_over", modal=True)

        DebugLogger.state(f"Game over shown (victory={victory})", category="game")

    def _find_element_by_id(self, root, element_id):
        """Recursively find element by id."""
        if hasattr(root, 'config') and root.config.get('id') == element_id:
            return root

        if hasattr(root, 'children'):
            for child in root.children:
                result = self._find_element_by_id(child, element_id)
                if result:
                    return result

        return None
        
    def _on_player_level_up(self, event):
        """Handle player level up event - show level up UI with 3 random upgrades."""
        self.scene_manager.pause_active_scene()
        self.ui.show_screen("level_up", modal=True)
        self.level_up_active = True
        DebugLogger.state(f"Player reached level {event.level}")
        
        # Generate 3 random upgrade options
        self._generate_random_upgrades()
        self._update_ui_buttons()
        
    def _on_upgrade_selected(self, event):
        """Handle upgrade selection - apply upgrade and continue game."""
        self.player.apply_upgrade(event.upgrade_type)
        self.level_up_active = False
        
        # Hide level up screen and resume game
        self.ui.hide_screen("level_up")
        self.scene_manager.resume_active_scene()
        
    def _generate_random_upgrades(self):
        """Generate 3 random upgrade options from available types."""
        all_upgrades = ["health", "damage", "speed", "firerate", "multishot"]
        self.available_upgrades = random.sample(all_upgrades, 3)
        
    def _update_ui_buttons(self):
        """Update the UI buttons with the available upgrades."""
        overlay = self.ui.screens.get("level_up")
        if not overlay:
            return
            
        # Mapping of upgrade types to display names
        upgrade_names = {
            "health": "Health +20%",
            "damage": "Damage +20%",
            "speed": "Speed +20%",
            "firerate": "Attack Speed +25%",
            "multishot": "Extra Shot"
        }
        
        # Mapping of upgrade types to colors
        upgrade_colors = {
            "health": [80, 60, 60],
            "damage": [60, 60, 80],
            "speed": [60, 80, 60],
            "firerate": [80, 60, 100],
            "multishot": [60, 100, 80]
        }
        
        # Update the 3 button elements
        for i in range(3):
            btn_id = f"upgrade_btn_{i+1}"
            btn_action = f"upgrade_{i+1}"
            btn = self._find_element_by_id(overlay, btn_id)
            
            if btn and i < len(self.available_upgrades):
                upgrade_type = self.available_upgrades[i]
                btn.text = upgrade_names[upgrade_type]
                btn.config["action"] = btn_action
                btn.background = upgrade_colors[upgrade_type]
                btn.mark_dirty()
    
    def _select_upgrade(self, upgrade_type):
        """Apply selected upgrade and close level up UI."""
        if self.level_up_active:
            # Apply the upgrade
            self.player.apply_upgrade(upgrade_type)
            
            # Dispatch upgrade event (for any listeners)
            get_events().dispatch(PlayerSelectedUpgradeEvent(upgrade_type=upgrade_type))
            
            # Set level up as inactive
            self.level_up_active = False
            
            # Hide level up screen and resume game
            self.ui.hide_screen("level_up")
            self.scene_manager.resume_active_scene()
            
            DebugLogger.state(f"Applied upgrade: {upgrade_type}", category="upgrade")
