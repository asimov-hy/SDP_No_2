"""
game_scene.py
-------------
Main gameplay scene - runs active level with player, enemies, bullets.
"""

import pygame
from src.scenes.base_scene import BaseScene
from src.systems.game_system_initializer import GameSystemInitializer
from src.core.runtime.game_settings import Debug
from src.systems.level.level_registry import LevelRegistry
from src.core.debug.debug_logger import DebugLogger


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
