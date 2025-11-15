"""
hud_manager.py
---------------
Defines the HUDManager system, responsible for assembling, positioning,
and updating all in-game Heads-Up Display elements.

Responsibilities
----------------
- Manage in-game overlays (health bar, score, exp bar, etc.).
- Handle component assembly, setting screen positions and layers.
- Interface with the global game state (STATE) to update element values.
- Provide the list of elements to the parent UIManager for rendering.
"""

from src.core.debug.debug_logger import DebugLogger
from src.ui.base_ui import *
from src.core.runtime.game_state import STATE


class HUDManager:
    """Manages the assembly and state of all HUD (Heads-Up Display) elements."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, screen_width, screen_height):
        """Initialize the HUD manager."""
        DebugLogger.init_sub("HUDManager Initialized")
        self.screen_width = screen_width
        self.screen_height = screen_height

        # List to hold all UI elements this manager owns.
        self.elements = []

        try:
            self._setup_elements()
            DebugLogger.init(f"HUDManager assembled {len(self.elements)} elements.")
        except pygame.error:
            DebugLogger.warn(f"[HUDManager] HUD setup fail")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, mouse_pos):
        """
        Update HUD elements (currently only used for passing mouse position).

        Args:
            mouse_pos (tuple): Mouse position for UI interactions.
        """
        pass

    # ===========================================================
    # Event Handling
    # ===========================================================
    def handle_event(self, event):
        """Handles input events (e.g., button clicks) for the HUD."""
        # Current implementation is empty, but the structure is now correct.
        pass

    def _setup_elements(self):
        """
        Internal helper method to assemble all HUD elements (Bars, Gauges, Images).
        """

        # === Top Exp Bar ===
        PATH_EXP_BAR_FRAME = "assets/images/UI/exp_bar.png"
        PATH_EXP_BAR_FILL = "assets/images/UI/current_exp.png" # Path assumed from context

        top_bar_fill = ExpCheck(
            x = 60,
            y = 48,
            fill_image_path = PATH_EXP_BAR_FILL,
            current_key='exp',
            max_key='level_exp',    # Assuming 'level_exp' is used for the max value
            layer=9
        )

        top_bar_frame = BaseImage(
            x = 32,
            y = 24,
            image_path=PATH_EXP_BAR_FRAME,
            layer=8
        )

        self.elements.append(top_bar_fill)
        self.elements.append(top_bar_frame)

        # === Bottom Health Gauge ===
        PATH_MAIN_BAR = "assets/images/UI/main_bar.png"
        PATH_HEALTH_GAUGE = "assets/images/UI/health_gauge.png"
        PATH_HEALTH_NEEDLE = "assets/images/UI/health_needle.png"

        main_bg = BaseImage(
            x = -2,
            y = 650,
            image_path=PATH_MAIN_BAR,
            layer=7
        )

        gauge_bg = BaseImage(
            x = 555,
            y = 620,
            image_path = PATH_HEALTH_GAUGE,
            layer=8
        )

        gauge_needle = GaugeNeedle(
            pivot_x = 630,
            pivot_y = 693,
            needle_image_path = PATH_HEALTH_NEEDLE,
            value_key='player_health',
            max_key='player_max_health',
            min_angle = -85,
            max_angle = 85,
            layer=9
        )

        self.elements.append(main_bg)
        self.elements.append(gauge_bg)
        self.elements.append(gauge_needle)

        DebugLogger.init("[HUDManager] HUD assembled successfully.")

    def get_elements(self):
        """
        Returns the list of all HUD elements managed by this instance.
        """
        return self.elements

    def update_values(self):
        """
        Updates the state of all managed HUD elements based on game data
        pulled directly from the global STATE object's player reference.
        """
        player = STATE.player_ref

        if player:
            current_health = player.health
            max_health = player.max_health

           # current_exp = getattr(player, 'exp', 0)
           # level_exp = getattr(player, 'level_exp', 100)

        game_data = {
            #'exp': current_exp,
            #'level_exp': level_exp,
            'player_health': current_health,
            'player_max_health': max_health
        }

        for elem in self.elements:
            elem.update_value(**game_data)