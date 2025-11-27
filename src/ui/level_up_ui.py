"""
level_up_ui.py
-------------
Simple level-up notification UI for the new architecture.
"""

import pygame
import time
from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Display


class LevelUpUI:
    """Simple level-up UI that shows upgrade choices."""

    def __init__(self, player):
        """
        Initialize level-up UI.

        Args:
            player: Player entity reference
        """
        self.player = player
        self.on_close = None

        # Position and size
        self.width, self.height = 600, 200
        self.x = (Display.WIDTH - self.width) // 2
        self.y = (Display.HEIGHT - self.height) // 2

        # State
        self.is_active = False
        self.choice_made = False

        self.selected_index = 0  # Currently selected upgrade
        self.hovered_index = None  # Mouse hover tracking

        # Upgrade choices
        self.upgrades = [
            {"name": "Health +1", "color": (192, 192, 192), "action": "health"},
            {"name": "Damage +10%", "color": (192, 192, 192), "action": "damage"},
            {"name": "Speed +10%", "color": (192, 192, 192), "action": "speed"}
        ]

        # Button areas
        self.button_height = 40
        self.button_margin = 15
        self.buttons = []
        self._setup_buttons()

        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 24)

        DebugLogger.init_entry("LevelUpUI initialized")

    def _setup_buttons(self):
        """Setup button rectangles horizontally."""
        button_width = 180
        button_y = self.y + 100
        total_width = button_width * 3 + self.button_margin * 2
        start_x = self.x + (self.width - total_width) // 2
        self.buttons = []

        for i in range(len(self.upgrades)):
            button_rect = pygame.Rect(
                start_x + i * (button_width + self.button_margin),
                button_y,
                button_width,
                self.button_height
            )
            self.buttons.append(button_rect)

    def show(self):
        """Show the level-up UI."""
        self.is_active = True
        self.choice_made = False
        self.selected_index = 0  # Reset to first option
        DebugLogger.state("LevelUpUI shown")

    def hide(self):
        """Hide the level-up UI."""
        self.is_active = False
        DebugLogger.state("LevelUpUI hidden", category="levelup")

        # Notify that UI closed (game scene can restore context)
        if self.on_close:
            self.on_close()

    def update(self, dt):
        """Update animations and hover state."""
        if not self.is_active:
            return

        # Track mouse hover
        mouse_pos = pygame.mouse.get_pos()
        self.hovered_index = None

        for i, button_rect in enumerate(self.buttons):
            if button_rect.collidepoint(mouse_pos):
                self.hovered_index = i
                # Auto-select on hover (optional - syncs keyboard with mouse)
                self.selected_index = i
                break

    def handle_input(self, input_manager):
        """Handle user input for upgrade selection."""
        if not self.is_active or self.choice_made:
            return

        # Use input_manager's action system (ui context)
        if input_manager.action_pressed("navigate_left"):
            self.selected_index = (self.selected_index - 1) % len(self.upgrades)
            DebugLogger.state(f"Selected upgrade {self.selected_index}")

        elif input_manager.action_pressed("navigate_right"):
            self.selected_index = (self.selected_index + 1) % len(self.upgrades)
            DebugLogger.state(f"Selected upgrade {self.selected_index}")

        # Confirm with Enter or Space
        if input_manager.action_pressed("confirm"):
            DebugLogger.state(f"Confirm pressed, applying upgrade {self.selected_index}")
            self._apply_upgrade(self.selected_index)

    def handle_event(self, event):
        """Handle pygame events (mouse clicks)."""
        if not self.is_active or self.choice_made:
            return False

        # Handle mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            mouse_pos = event.pos

            for i, button_rect in enumerate(self.buttons):
                if button_rect.collidepoint(mouse_pos):
                    DebugLogger.state(f"Mouse clicked upgrade {i}")
                    self._apply_upgrade(i)
                    return True  # Event consumed

        return False  # Event not consumed

    def _apply_upgrade(self, index):
        """Apply the selected upgrade."""
        if index >= len(self.upgrades):
            return

        upgrade = self.upgrades[index]
        action = upgrade["action"]

        if action == "health":
            self.player.max_health += 1
            self.player.health = self.player.max_health
        elif action == "damage":
            if hasattr(self.player, 'damage'):
                self.player.damage = int(self.player.damage * 1.1)
        elif action == "speed":
            self.player.base_speed *= 1.1

        DebugLogger.state(f"Applied upgrade: {upgrade['name']}", category="levelup")
        self.choice_made = True
        self.hide()

    def draw(self, draw_manager):
        """Draw the level-up UI."""
        if not self.is_active:
            return

        # Create surface
        surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        # Background
        pygame.draw.rect(surface, (40, 40, 50), surface.get_rect(), border_radius=8)
        pygame.draw.rect(surface, (200, 200, 255), surface.get_rect(), 2, border_radius=8)

        # Title
        title_text = f"LEVEL {self.player.level}!"
        title_surface = self.title_font.render(title_text, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.width // 2, 30))
        surface.blit(title_surface, title_rect)

        # Subtitle
        subtitle_text = "Choose an upgrade:"
        subtitle_surface = self.button_font.render(subtitle_text, True, (200, 200, 200))
        subtitle_rect = subtitle_surface.get_rect(center=(self.width // 2, 60))
        surface.blit(subtitle_surface, subtitle_rect)

        # Inside draw() method, button rendering:
        for i, (upgrade, button_rect) in enumerate(zip(self.upgrades, self.buttons)):
            local_rect = pygame.Rect(
                button_rect.x - self.x,
                button_rect.y - self.y,
                button_rect.width,
                button_rect.height
            )

            pygame.draw.rect(surface, upgrade["color"], local_rect, border_radius=5)

            # Use hover effect for both keyboard and mouse
            is_active = (i == self.selected_index or i == self.hovered_index)

            # Brighten color when active (hover effect)
            button_color = upgrade["color"]
            if is_active:
                # Brighten by 30 RGB units
                button_color = tuple(min(c + 30, 255) for c in button_color)

            pygame.draw.rect(surface, button_color, local_rect, border_radius=5)
            pygame.draw.rect(surface, (255, 255, 255), local_rect, 1, border_radius=5)  # Subtle border

            text_surface = self.button_font.render(upgrade["name"], True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=local_rect.center)
            surface.blit(text_surface, text_rect)

        # Draw to screen using DrawManager's queue_draw method
        draw_manager.queue_draw(surface, pygame.Rect(self.x, self.y, self.width, self.height), layer=200)

    def cleanup(self):
        """Cleanup resources."""
        self.is_active = False
        DebugLogger.state("LevelUpUI cleaned up", category="levelup")