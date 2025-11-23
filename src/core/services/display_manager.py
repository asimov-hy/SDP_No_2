"""
display_manager.py
------------------
Handles all window management, scaling, and rendering operations
while preserving a fixed 16:9 aspect ratio.

Responsibilities
----------------
- Manage window creation and fullscreen toggling.
- Maintain consistent scaling and letterboxing across resolutions.
- Provide coordinate conversions (screen ↔ game space).
- Handle render scaling and resizing behavior.
- Support preset window sizes (user resizing disabled).
"""

import pygame
from pygame.display import is_fullscreen

from src.core.debug.debug_logger import DebugLogger


class DisplayManager:
    """
    Handles window management, scaling, and borderless fullscreen with fixed 16:9 aspect ratio.

    Architecture: Software Scaling
    -------------------------------
    This implementation uses CPU-based software scaling via pygame.transform.scale().
    While this has performance overhead (~2ms per frame at 1080p), it provides:
    - Guaranteed correct behavior across all platforms
    - Precise control over window sizing
    - Reliable mouse coordinate mapping
    - Support for window size presets

    The pygame.SCALED hardware acceleration was considered but abandoned due to:
    - Uncertain mouse coordinate remapping behavior
    - Incompatibility with programmatic window sizing
    - Platform-dependent behavior
    - Minimal performance gain for 2D bullet hell game
    """

    # ===========================================================
    # Initialization
    # ===========================================================

    def __init__(self, game_width=1280, game_height=720, window_size="small"):
        """
        Initialize window, scaling values, and render surface.

        Args:
            game_width (int): Logical game resolution width.
            game_height (int): Logical game resolution height.
            window_size (str): Initial window size preset ("small", "medium", "large").
        """
        DebugLogger.init_entry("DisplayManager")

        # Core Setup
        self.game_width = game_width
        self.game_height = game_height
        self.window_size_preset = window_size
        self.game_surface = pygame.Surface((game_width, game_height))

        # State flags
        self.is_fullscreen = False
        self.window = None

        # Scaling & Letterboxing (calculated in _calculate_scale)
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.scaled_size = (game_width, game_height)

        # Render Caches (optimization to avoid recreating surfaces every frame)
        self.letterbox_bars = None
        self.scaled_surface_cache = None
        self.cached_subsurface_rect = None
        self.display_dirty = True

        # Window Creation
        self._create_window(silent=True)
        mode = "Fullscreen" if is_fullscreen() else f"Windowed ({game_width}x{game_height})"
        DebugLogger.init_sub(f"Display Mode: {mode}", level=1)

    # ===========================================================
    # Window Creation and Scaling
    # ===========================================================

    def _create_window(self, fullscreen=False, silent=False):
        """
        Create the pygame window with appropriate flags.

        Architecture Notes:
        - Fullscreen mode: Uses native resolution, no resizing
        - Windowed mode: Uses preset physical size, allows user resizing
        - RESIZABLE flag: Allows users to drag window corners (UX improvement)

        Args:
            fullscreen (bool): Whether to create fullscreen window.
            silent (bool): If True, suppress debug logging.
        """
        if fullscreen:
            # Fullscreen: Let pygame choose native resolution
            self.window = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.HWSURFACE
            )
            self.is_fullscreen = True
        else:
            # Windowed: Use preset size (fixed - resizing disabled)
            from src.core.runtime.game_settings import Display
            window_w, window_h = Display.WINDOW_SIZES.get(
                self.window_size_preset,
                (self.game_width, self.game_height)
            )

            self.window = pygame.display.set_mode(
                (window_w, window_h),
                pygame.DOUBLEBUF | pygame.HWSURFACE
            )
            self.is_fullscreen = False

        # Calculate scaling factors for aspect ratio preservation
        self._calculate_scale()

        if not silent:
            mode = "Fullscreen" if fullscreen else f"Windowed ({window_w}x{window_h})"
            DebugLogger.init_sub(f"Display Mode: {mode}", level=1)

    def _calculate_scale(self):
        """
        Calculate scale factor and letterbox offsets to maintain 16:9 aspect ratio.

        This method is critical for:
        1. Aspect ratio preservation (no stretching on non-16:9 displays)
        2. Mouse coordinate mapping (screen → game space)
        3. Letterbox positioning (black bars on sides/top/bottom)

        Called when:
        - Window is created
        - Window is resized by user
        - Fullscreen mode is toggled
        - Window size preset is changed
        """
        window_width, window_height = self.window.get_size()

        # Determine scale based on smallest dimension to avoid stretching
        scale_x = window_width / self.game_width
        scale_y = window_height / self.game_height
        self.scale = min(scale_x, scale_y)

        # Compute scaled dimensions that preserve aspect ratio
        scaled_width = int(self.game_width * self.scale)
        scaled_height = int(self.game_height * self.scale)

        # Center the scaled surface (creates letterboxing effect)
        self.offset_x = (window_width - scaled_width) // 2
        self.offset_y = (window_height - scaled_height) // 2

        # Pre-create letterbox bar surfaces (optimization)
        self._create_letterbox_bars()

        self.scaled_size = (scaled_width, scaled_height)
        self.display_dirty = True  # Mark for cache refresh

        DebugLogger.trace(
            f"Scale={self.scale:.3f}, Offset=({self.offset_x},{self.offset_y})",
            category="display"
        )

    def _create_letterbox_bars(self):
        """
        Pre-create black bar surfaces for letterboxing.

        Optimization: Creating surfaces once here is faster than filling
        the entire window with black every frame.

        Letterbox bars appear when:
        - Window aspect ratio ≠ 16:9
        - Vertical bars (sides): Window is wider than 16:9
        - Horizontal bars (top/bottom): Window is taller than 16:9
        """
        window_width, window_height = self.window.get_size()

        if self.offset_x > 0:  # Vertical bars (window too wide)
            self.letterbox_bars = [
                (pygame.Surface((self.offset_x, window_height)), (0, 0)),  # Left bar
                (pygame.Surface((self.offset_x, window_height)),
                 (window_width - self.offset_x, 0))  # Right bar
            ]
            for surf, _ in self.letterbox_bars:
                surf.fill((0, 0, 0))

        elif self.offset_y > 0:  # Horizontal bars (window too tall)
            self.letterbox_bars = [
                (pygame.Surface((window_width, self.offset_y)), (0, 0)),  # Top bar
                (pygame.Surface((window_width, self.offset_y)),
                 (0, window_height - self.offset_y))  # Bottom bar
            ]
            for surf, _ in self.letterbox_bars:
                surf.fill((0, 0, 0))

        else:  # Perfect 16:9 aspect ratio - no bars needed
            self.letterbox_bars = None

    # ===========================================================
    # Window Actions
    # ===========================================================

    def toggle_fullscreen(self):
        """
        Toggle between windowed and fullscreen modes.

        Recreates the window entirely to switch modes.
        Preserves the window size preset for when returning to windowed mode.
        """
        self._create_window(not self.is_fullscreen)
        state = "ON" if self.is_fullscreen else "OFF"
        DebugLogger.state(f"Toggled fullscreen → {state}", category="display")

    def set_window_size(self, size_preset):
        """
        Programmatically change window size to a preset.

        Available presets (defined in game_settings.py):
        - "small": 1280x720 (720p)
        - "medium": 1920x1080 (1080p)
        - "large": 2560x1440 (1440p)

        Args:
            size_preset (str): Preset name ("small", "medium", "large").
        """
        if self.is_fullscreen:
            DebugLogger.warn("Cannot change window size in fullscreen mode")
            return

        from src.core.runtime.game_settings import Display
        if size_preset not in Display.WINDOW_SIZES:
            DebugLogger.warn(f"Unknown window size preset: {size_preset}")
            return

        # Update preset and get new dimensions
        self.window_size_preset = size_preset
        window_w, window_h = Display.WINDOW_SIZES[size_preset]

        # Recreate window with new size
        self.window = pygame.display.set_mode(
            (window_w, window_h),
            pygame.DOUBLEBUF | pygame.HWSURFACE
        )
        self._calculate_scale()

        DebugLogger.state(f"Window size changed to {size_preset}: {window_w}x{window_h}")

    # ===========================================================
    # Rendering Pipeline
    # ===========================================================

    def get_game_surface(self):
        """
        Get the surface that game elements should draw to.

        Returns:
            pygame.Surface: The logical game surface (always 1280x720).
        """
        return self.game_surface

    def render(self):
        """
        Scale and render the game surface to the actual window with letterboxing.

        Performance Note:
        -----------------
        pygame.transform.scale() is expensive (~2ms at 1080p) but necessary
        because game_surface content changes every frame (bullets move, etc.).

        Optimizations applied:
        1. Letterbox bars cached and only redrawn when window resizes
        2. Subsurface caching to avoid destination surface recreation
        3. dest_surface parameter to avoid temporary surface allocation

        Alternative considered: pygame.SCALED flag (hardware acceleration)
        - Rejected due to platform inconsistencies and lost functionality
        - See class docstring for detailed reasoning
        """
        # Refresh letterbox bars only when window size changes
        if self.display_dirty:
            if self.letterbox_bars:
                # Blit pre-created black bar surfaces
                for surf, pos in self.letterbox_bars:
                    self.window.blit(surf, pos)
            else:
                # No letterboxing needed - fill entire window
                self.window.fill((0, 0, 0))

            # Cache the subsurface destination to avoid recreation every frame
            self.cached_subsurface_rect = pygame.Rect(
                self.offset_x, self.offset_y,
                self.scaled_size[0], self.scaled_size[1]
            )
            self.scaled_surface_cache = self.window.subsurface(self.cached_subsurface_rect)
            self.display_dirty = False

        # CRITICAL: Software scaling operation (expensive but necessary)
        # Scales 1280x720 game_surface to physical window dimensions
        pygame.transform.scale(
            self.game_surface,
            self.scaled_size,
            dest_surface=self.scaled_surface_cache  # Avoids temp surface allocation
        )

        pygame.display.flip()

    # ===========================================================
    # Coordinate Utilities
    # ===========================================================

    def screen_to_game_pos(self, screen_x, screen_y):
        """
        Convert window (physical) coordinates to game-space (logical) coordinates.

        Critical for mouse input to work correctly across different window sizes.

        Example:
        - Window: 1920x1080, Game: 1280x720
        - Mouse click at physical (1920, 1080)
        - Returns logical (1280, 720)

        Math:
        1. Subtract letterbox offset (handles centering)
        2. Divide by scale factor (handles different resolutions)

        Args:
            screen_x (float): X position in window/physical space.
            screen_y (float): Y position in window/physical space.

        Returns:
            tuple[float, float]: (x, y) position in game/logical space.
        """
        game_x = (screen_x - self.offset_x) / self.scale
        game_y = (screen_y - self.offset_y) / self.scale
        return game_x, game_y

    def is_in_game_area(self, screen_x, screen_y):
        """
        Check if physical screen coordinates are inside the rendered game area.

        Returns False if clicking on letterbox bars (black borders).
        Useful for UI hit detection and input validation.

        Args:
            screen_x (float): X position in window space.
            screen_y (float): Y position in window space.

        Returns:
            bool: True if coordinates are within the active game area.
        """
        game_x, game_y = self.screen_to_game_pos(screen_x, screen_y)
        return (0 <= game_x <= self.game_width and
                0 <= game_y <= self.game_height)

    def get_window_size(self):
        """
        Get the current physical window size.

        Returns:
            tuple[int, int]: (width, height) of the actual pygame window in pixels.
        """
        return self.window.get_size()

    def mark_dirty(self):
        """
        Force display to refresh letterbox bars and caches on next render.

        Call this when:
        - Window is manually repositioned
        - Display settings change externally
        - Forcing a complete re-render for debugging
        """
        self.display_dirty = True