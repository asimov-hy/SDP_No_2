"""
level_up_screen.py
------------------
Level-up screen using YAML-driven UI system.
Randomly selects upgrades from JSON config.
"""

import json
import random
from pathlib import Path
from src.core.debug.debug_logger import DebugLogger
from src.entities.player.player_effects import EFFECT_HANDLERS


class LevelUp:
    """Level-up UI - logic only, visuals from YAML."""

    def __init__(self, player, ui_manager):
        self.player = player
        self.ui_manager = ui_manager
        self.on_close = None

        # Load all available upgrades
        self.all_upgrades = self._load_upgrades_config()

        # Current random selection (set on show())
        self.current_choices = []

        # Load UI from YAML
        ui_manager.load_screen("level_up", "screens/level_up.yaml")

        self.is_active = False
        DebugLogger.init_entry("LevelUp initialized")

    def _load_upgrades_config(self):
        """Load upgrade definitions from JSON."""
        path = Path("src/config/player/upgrades.json")
        if not path.exists():
            DebugLogger.warn("upgrades.json not found", category="ui")
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def show(self):
        """Show level-up UI with random upgrade choices."""
        # Pick 3 random upgrades
        self._select_random_upgrades(3)

        # Update button visuals
        self._update_buttons()

        # Show screen
        self.ui_manager.show_screen("level_up", modal=True)
        self.is_active = True

        DebugLogger.state(
            f"LevelUp shown with: {[u['id'] for u in self.current_choices]}",
            category="levelup",
        )

    def _select_random_upgrades(self, count: int):
        """Select random upgrades from pool."""
        upgrade_ids = list(self.all_upgrades.keys())

        # Clamp count to available upgrades
        count = min(count, len(upgrade_ids))

        # Random selection
        selected_ids = random.sample(upgrade_ids, count)

        # Build choice list with full data
        self.current_choices = []
        for uid in selected_ids:
            data = self.all_upgrades[uid]
            self.current_choices.append(
                {
                    "id": uid,
                    "name": data.get("name", uid),
                    "color": tuple(data.get("color", [192, 192, 192])),
                    "effects": data.get("effects", []),
                }
            )

    def _update_buttons(self):
        """Update button text/color/action for current choices."""
        for i, upgrade in enumerate(self.current_choices):
            button = self.ui_manager.find_element_by_id("level_up", f"upgrade_slot_{i}")
            if button:
                # Reset focus state
                button.is_focused = False
                button.hover_t = 0.0
                # Update visuals
                button.text = upgrade["name"]
                button.color = upgrade["color"]
                button.action = f"upgrade_{upgrade['id']}"
                button.mark_dirty()

    def hide(self):
        """Hide level-up UI."""
        self.ui_manager.hide_screen("level_up")
        self.is_active = False
        if self.on_close:
            self.on_close()

    def handle_action(self, action: str) -> bool:
        """Handle button clicks from game_scene."""
        if not action or not action.startswith("upgrade_"):
            return False

        upgrade_id = action.replace("upgrade_", "")
        self._apply_upgrade(upgrade_id)
        return True

    def _apply_upgrade(self, upgrade_id: str):
        """Apply upgrade effects."""
        upgrade = self.all_upgrades.get(upgrade_id)
        if not upgrade:
            DebugLogger.warn(f"Unknown upgrade: {upgrade_id}", category="levelup")
            return

        for effect in upgrade.get("effects", []):
            handler = EFFECT_HANDLERS.get(effect["type"])
            if handler:
                handler(self.player, effect)
            else:
                self._apply_local_effect(effect)

        DebugLogger.state(f"Applied: {upgrade['name']}", category="levelup")
        self.hide()

    def _apply_local_effect(self, effect):
        """Fallback for effects not in EFFECT_HANDLERS."""
        effect_type = effect.get("type")

        if effect_type == "ADD_MAX_HEALTH":
            self.player.max_health += effect.get("amount", 1)
        elif effect_type == "MULTIPLY_DAMAGE":
            if hasattr(self.player, "damage"):
                self.player.damage = int(
                    self.player.damage * effect.get("multiplier", 1.0)
                )
        elif effect_type == "MULTIPLY_SPEED":
            self.player.base_speed *= effect.get("multiplier", 1.0)

    def cleanup(self):
        """Cleanup resources."""
        self.is_active = False
