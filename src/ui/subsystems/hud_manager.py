"""
hud_manager.py
---------------
Temporary placeholder for the HUDManager system.
Used to satisfy imports during development.

Responsibilities
----------------
- Manage in-game overlays (health bar, score, ammo, etc.).
- Handle temporary UI like damage flashes or debug HUD.
- Interface with UIManager for rendering.

NOTE:
This is a stub implementation and currently inactive.
"""

from src.core.utils.debug_logger import DebugLogger
from src.ui.ui_element import *

class HUDManager:
    """
    Manages the assembly and state of all HUD (Heads-Up Display) elements.

    This class is responsible for initializing all individual HUD components
    (like bars, gauges, and images), setting their screen positions and
    rendering layers, and providing a single interface to update their
    values based on game data.

    It owns the list of elements that will be passed to a more general
    UIManager, which will handle the actual rendering loop.
    """

    def __init__(self, screen_width, screen_height):
        """
        Initializes the HUDManager.

        Stores screen dimensions and immediately calls the internal
        _setup_elements() method to build the HUD component list.
        Includes error handling to catch fatal errors during setup.

        Args:
            screen_width (int): The width of the game screen.
            screen_height (int): The height of the game screen.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # List to hold all UI elements this manager owns.
        self.elements = []

        try:
            self._setup_elements()
            DebugLogger.init(f"HUDManager assembled {len(self.elements)} elements.")
        except pygame.error:
            DebugLogger.warn(f"[HUDManager] HUD setup fail")

    def _setup_elements(self):
        """
        Internal helper method to assemble all HUD elements.

        This method is responsible for instantiating all the individual
        UI elements (BaseImage, ExpCheck, GaugeNeedle) that make up
        the HUD. It defines their assets, screen positions, rendering
        layers, and the data keys they will use for updates.

        Note: The order of appending to self.elements does not strictly
        matter, as the UIManager is expected to sort them by 'layer'
        before rendering.
        """

        # === Top Exp Bar ===
        PATH_EXP_BAR_FRAME = "assets/images/UI/exp_bar.png"
        PATH_EXP_BAR_FILL = "assets/images/UI/current_exp.png"

        # Create the fill element (ExpCheck).
        # It renders at layer 101, behind the frame.
        top_bar_fill = ExpCheck(
            x = 60,
            y = 48,
            fill_image_path = PATH_EXP_BAR_FILL,
            current_key='exp',      # Key for update_values
            max_key='max_exp',
            layer=101
        )

        # Create the frame element (BaseImage).
        # It renders at layer 102, *on top of* the fill.
        top_bar_frame = BaseImage(
            x = 32,
            y = 24,
            image_path=PATH_EXP_BAR_FRAME,
            layer=102               # Renders *on top of* the fill
        )

        # Add elements to the managed list.
        self.elements.append(top_bar_fill)
        self.elements.append(top_bar_frame)

        # === Bottom Health Gauge ===
        PATH_MAIN_BAR = "assets/images/UI/main_bar.png"
        PATH_HEALTH_GAUGE = "assets/images/UI/health_gauge.png"
        PATH_HEALTH_NEEDLE = "assets/images/UI/health_needle.png"

        # Create the main background bar.
        # Renders at layer 100
        main_bg = BaseImage(
            x = -2,
            y = 650,
            image_path=PATH_MAIN_BAR,
            layer=100               # Renders at the very bottom
        )

        # Create the static gauge background.
        # Renders at layer 101
        gauge_bg = BaseImage(
            x = 555,
            y = 620,
            image_path = PATH_HEALTH_GAUGE,
            layer=101
        )

        # Create the dynamic rotating needle.
        # Renders at layer 102
        gauge_needle = GaugeNeedle(
            pivot_x = 630,  # rotation center
            pivot_y = 693,  # rotation center
            needle_image_path = PATH_HEALTH_NEEDLE,
            value_key='player_health',
            max_key='player_max_health',
            min_angle = -85,
            max_angle = 85,
            layer=102       # Renders on top of the gauge
        )

        # Add elements to the managed list.
        self.elements.append(main_bg)
        self.elements.append(gauge_bg)
        self.elements.append(gauge_needle)

        DebugLogger.system("[HUDManager] HUD assembled successfully.")

    def get_elements(self):
        """
        Returns the list of all HUD elements managed by this instance.

        This allows a central UIManager to retrieve all elements
        that need to be updated and rendered.

        Returns:
            list[UIElement]: The list of all initialized HUD elements.
        """
        return self.elements

    def update_values(self, game_data_dict):
        """
        Updates the state of all managed HUD elements based on game data.
        """
        for elem in self.elements:
            # Pass the entire data dictionary.
            # Each element will find the keys it cares about.
            elem.update_value(**game_data_dict)
