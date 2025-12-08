"""
main_menu_scene.py
------------------
Main menu - title, start game, settings, quit.
"""

import pygame
from src.core.services.config_manager import load_config

from src.scenes.base_scene import BaseScene
from src.scenes.transitions.transitions import FadeTransition

from src.graphics.particles.particle_manager import ParticleOverlay


class MainMenuScene(BaseScene):
    """Main menu scene with navigation."""

    BACKGROUNDS_PATH = "assets/images/backgrounds/"

    BACKGROUND_CONFIG = {
        "layers": [
            {
                "image": BACKGROUNDS_PATH + "main_menu.png",
                "scroll_speed": [0, 0],
                "parallax": [0, 0],
            }
        ]
    }

    def __init__(self, services):
        super().__init__(services)
        self.input_context = "ui"
        self.ui = services.ui_manager
        self.particles = []

    def on_enter(self):
        """Called when scene becomes active."""
        self._setup_background(self.BACKGROUND_CONFIG)
        self._load_particles()

        self.ui.clear_hud()
        self.ui.hide_all_screens()
        self.ui.load_screen("main_menu", "screens/main_menu.yaml")
        self.ui.show_screen("main_menu")
        menu_sound = self.services.get_global("sound_manager")
        menu_sound.play_bgm("menu_bgm", loop=-1)

    def on_exit(self):
        """Called when leaving scene."""
        self._clear_background()
        self.ui.hide_screen("main_menu")
        for p in self.particles:
            p.clear()
        self.particles.clear()

    def update(self, dt: float):
        """Update menu logic."""
        self._update_background(dt)
        for p in self.particles:
            p.update(dt)

        mouse_pos = self.input_manager.get_effective_mouse_pos()
        self.ui.update(dt, mouse_pos)

    def draw(self, draw_manager):
        """Render menu."""
        for p in self.particles:
            p.render(draw_manager)

        self.ui.draw(draw_manager)

    def handle_event(self, event):
        """Handle input events."""
        action = self.ui.handle_event(event)

        if action == "start_game":
            self.scene_manager.set_scene(
                "CampaignSelect", transition=FadeTransition(0.4)
            )
        elif action == "settings":
            self.scene_manager.set_scene(
                "Settings", transition=FadeTransition(0.3), caller="MainMenu"
            )
        elif action == "quit":
            pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _load_particles(self):
        """Load particle emitters from screen config."""

        config = load_config("main_menu.yaml")

        particle_data = config.get("main_menu", {}).get("particles", [])

        for p in particle_data:
            overlay = ParticleOverlay(
                p["preset"],
                max_particles=p.get("max_particles", 100),
                spawn_rate=p.get("spawn_rate", 25),
                spawn_area=tuple(p["spawn_area"]) if p.get("spawn_area") else None,
                direction=tuple(p["direction"]) if p.get("direction") else None,
                speed=tuple(p["speed"]) if p.get("speed") else None,
                lifetime=tuple(p["lifetime"]) if p.get("lifetime") else None,  # ADD
            )
            self.particles.append(overlay)
