"""
game_scene.py
-------------
Main gameplay scene handling player, enemies, bullets, and level progression.

Game Over Flow:
    1. Level complete or player death triggers game over
    2. Delay timer starts (configurable pause before overlay)
    3. Screen fades to dark overlay
    4. Stats reveal one-by-one with timed intervals
    5. Player can return to menu

Features:
    - Level loading and campaign progression
    - Player, enemy, bullet management
    - Collision detection
    - Game over / victory handling with animated stats
    - Background parallax integration
"""

import pygame

# Core - Debug & Settings
from src.core.debug.debug_logger import DebugLogger
from src.core.runtime.game_settings import Debug, Display
from src.core.runtime.session_stats import get_session_stats

# Core - Runtime & Services
from src.core.services.event_manager import (
    get_events,
    EnemyDiedEvent,
    ScreenShakeEvent,
    SpawnPauseEvent,
)

# Entities
from src.entities.entity_state import LifecycleState

# Graphics - Particles
from src.graphics.particles.particle_manager import ParticleEmitter

# Scenes
from src.scenes.base_scene import BaseScene
from src.scenes.scene_state import SceneState
from src.scenes.transitions.transitions import FadeTransition, UIFadeOverlay

from src.scenes.cutscenes.cutscene_manager import CutsceneManager
from src.scenes.cutscenes.cutscene_action import (
    ActionGroup,
    DelayAction,
    CallbackAction,
    LockInputAction,
    MoveEntityAction,
    TextFlashAction,
    UISlideInAction,
    TextScaleFadeAction,
    TextBlinkRevealAction,
)

# Systems
from src.systems.game_system_initializer import GameSystemInitializer

# UI
from src.scenes.level_up_screen import LevelUp


# ===========================================================
# Constants
# ===========================================================

MAPS_PATH = "assets/images/maps/"
BGM_PATH = "assets/audio/bgm/"

# Default background for levels without explicit config
DEFAULT_BACKGROUND = {
    "layers": [
        {
            "image": "assets/images/null.png",
            "scroll_speed": [0, -300],
            "parallax": [0.4, -0.4]
        }
    ]
}

# Game over timing configuration
DEFAULT_MUSIC = "IngameBGM"
GAME_OVER_DELAY = 2           # Seconds before game over screen appears
GAME_OVER_FADE_SPEED = 200      # Overlay fade speed (lower = slower)
STAT_REVEAL_DELAY = 0.4         # Seconds between each stat reveal


class GameScene(BaseScene):
    """
    Active gameplay scene.

    Manages all gameplay systems including player, enemies, bullets,
    collisions, and level progression. Handles game over with
    animated stat reveals.
    """

    # ===========================================================
    # Initialization
    # ===========================================================

    def __init__(self, services):
        """
        Initialize gameplay scene and all subsystems.

        Args:
            services: ServiceLocator for dependency injection
        """
        super().__init__(services)
        self.input_context = "gameplay"

        DebugLogger.section("Initializing GameScene")

        # --- Core Systems ---
        self._init_systems(services)

        # --- Campaign State ---
        self.campaign = None
        self.current_level_idx = 0
        self.selected_level_id = None

        # --- Game State ---
        self.game_over_shown = False

        # --- Game Over State ---
        # Delay timer before showing game over screen
        self._game_over_pending = False
        self._game_over_victory = False
        self._game_over_delay_timer = 0.0

        # Stat reveal animation state
        self._stat_reveal_queue = []        # Labels waiting to be revealed
        self._stat_reveal_timer = 0.0       # Timer for next reveal
        self._stat_values = {}              # Cached stat text values

        # --- UI Systems ---
        self._init_level_up_ui()

        # Overlay for pause/game over (semi-transparent dark tint)
        self.overlay = UIFadeOverlay(color=(0, 0, 0), max_alpha=150)

        # Cutscene system
        self.cutscene_manager = CutsceneManager()
        self._intro_complete = False

        # --- Event Subscriptions ---
        self.level_manager.on_level_complete = self._on_level_complete
        get_events().subscribe(EnemyDiedEvent, self._on_enemy_died)

        DebugLogger.section("GameScene Initialized")

    def _init_systems(self, services):
        """
        Initialize all game subsystems via GameSystemInitializer.

        Args:
            services: ServiceLocator instance
        """
        initializer = GameSystemInitializer(services)
        systems = initializer.initialize()

        # Store system references for easy access
        self.player = systems['player']
        self.player.sound_manager = services.get_global("sound_manager")
        self.collision_manager = systems['collision_manager']
        self.spawn_manager = systems['spawn_manager']
        self.bullet_manager = systems['bullet_manager']
        self.level_manager = systems['level_manager']
        self.effects_manager = systems['effects_manager']
        self.hazard_manager = systems['hazard_manager']
        self.spawn_manager._effects_manager = self.effects_manager
        self.ui = systems['ui']
        self.player.services = self.services



    def _init_level_up_ui(self):
        """Initialize level up UI overlay."""
        self.level_up_ui = LevelUp(self.player, self.ui)
        self.level_up_ui.on_close = lambda: self.input_manager.set_context("gameplay")
        self.last_player_level = self.player.level

    # ===========================================================
    # Lifecycle Hooks
    # ===========================================================

    def on_load(self, campaign_name=None, level_id=None, **scene_data):
        """
        Load campaign data when scene is created.

        Called by SceneManager before on_enter().

        Args:
            campaign_name: Name of campaign to load
            level_id: Specific level ID to start (overrides campaign)
            **scene_data: Additional scene parameters
        """
        self.selected_level_id = level_id
        level_registry = self.services.get_global("level_registry")

        if campaign_name:
            self.campaign = level_registry.get_campaign(campaign_name)
            if self.campaign:
                DebugLogger.init_sub(
                    f"Loaded campaign: {campaign_name} ({len(self.campaign)} levels)"
                )
            else:
                DebugLogger.warn(f"Campaign '{campaign_name}' not found")
                self.campaign = []
        else:
            # Default campaign fallback
            self.campaign = level_registry.get_campaign("test")
            if self.campaign:
                DebugLogger.init_sub(
                    f"Loaded default campaign: test ({len(self.campaign)} levels)"
                )
            else:
                self.campaign = []

    def on_enter(self):
        """
        Start gameplay when scene becomes active.

        Called after transition completes. Sets up audio, UI, and starts level.
        """
        # Audio

        # UI setup
        self.ui.register_binding('player', self.player)
        self.ui.load_hud("hud/player_hud.yaml")
        # Hide HUD initially - cutscene will slide it in
        self._hide_hud_for_intro()
        self.ui.load_screen("game_over", "screens/game_over.yaml")

        # Reset all game state
        self.game_over_shown = False
        self._game_over_pending = False
        self._game_over_delay_timer = 0.0
        self._stat_reveal_queue = []
        get_session_stats().reset()

        # Subscribe to screen shake events
        get_events().subscribe(ScreenShakeEvent, self._on_screen_shake)

        # Start level (loads but doesn't spawn yet)
        self._start_level()

        # Play intro cutscene
        self._play_intro_cutscene()

    def _hide_hud_for_intro(self):
        """Hide HUD elements off-screen before intro cutscene."""
        for element in self.ui.hud_elements:
            anchor = getattr(element, 'parent_anchor', 'center')
            offset = self.ui.ANCHOR_TO_OFFSET.get(anchor, (0, -300))
            element._slide_offset = offset

    def on_exit(self):
        """
        Clean up when leaving gameplay.

        Called before transitioning to another scene.
        """
        ParticleEmitter.clear_all()
        self.effects_manager.clear()
        self._clear_background()
        self.ui.clear_hud()
        self.ui.hide_screen("game_over")

    def on_pause(self):
        """Pause gameplay and show pause overlay."""
        self.pause_background()
        self.ui.show_screen("pause", modal=True, slide_from="top", slide_duration=0.2)
        self.overlay.fade_in(speed=600)

    def on_resume(self):
        """Resume gameplay from pause."""
        self.resume_background()
        self.overlay.fade_out(speed=400)
        self.ui.hide_screen("pause", slide_to="top", slide_duration=0.25)

    # ===========================================================
    # Intro Cutscene
    # ===========================================================

    def _play_intro_cutscene(self):
        """Build and play level intro cutscene."""

        # Pause spawning during intro
        get_events().dispatch(SpawnPauseEvent(paused=True))

        # Player start/end positions
        center_x = Display.WIDTH / 2
        start_y = Display.HEIGHT + self.player.rect.height
        end_y = Display.HEIGHT / 2

        actions = [
            # Phase 1: Lock input, position player off-screen, pause BG scroll
            ActionGroup([
                LockInputAction(self.player, locked=True),
                CallbackAction(self._position_player_offscreen),
            ]),

            # Phase 2: Player flies in
            MoveEntityAction(
                entity=self.player,
                start_pos=(center_x, start_y),
                end_pos=(center_x, end_y),
                duration=1.0,
                easing="ease_out"
            ),

            # Phase 3: UI slides in + System text with effects
            ActionGroup([
                UISlideInAction(self.ui, duration=0.4, stagger=0.4),
                TextScaleFadeAction(
                    "MAIN SYSTEM",
                    duration=0.5,
                    start_scale=1.6,
                    end_scale=1.0,
                    font_size=36,
                    hold_time=1.5,
                    fade_out=0.2,
                    y_offset=-40
                ),
                TextScaleFadeAction(
                    "---",
                    duration=0.5,
                    start_scale=1.5,
                    end_scale=1.0,
                    font_size=36,
                    hold_time=1.5,
                    fade_out=0.2,
                    y_offset=0
                ),
                TextScaleFadeAction(
                    "COMBAT MODE ACTIVE",
                    duration=0.5,
                    start_scale=1.6,
                    end_scale=1.0,
                    font_size=28,
                    hold_time=1.5,
                    fade_out=0.2,
                    y_offset=40
                ),
            ]),

            # Phase 4: Commence mission with blink effect
            TextBlinkRevealAction(
                "COMMENCE MISSION",
                duration=1.2,
                font_size=48,
                blink_count=10,
                hold_time=1.0,
                fade_out=0.3
            ),

            # Phase 5: Enable gameplay
            ActionGroup([
                LockInputAction(self.player, locked=False),
                CallbackAction(self._on_intro_complete),
            ]),
        ]

        self.cutscene_manager.play(actions)

    def _on_intro_complete(self):
        """Called when intro cutscene finishes."""
        self._intro_complete = True
        # Resume spawning
        get_events().dispatch(SpawnPauseEvent(paused=False))

    def _position_player_offscreen(self):
        """Move player to starting position off-screen."""
        self.player.rect.centerx = Display.WIDTH / 2
        self.player.rect.centery = Display.HEIGHT + 50
        self.player.virtual_pos.x = self.player.rect.centerx
        self.player.virtual_pos.y = self.player.rect.centery

    # ===========================================================
    # Level Loading
    # ===========================================================

    def _start_level(self):
        """
        Start the appropriate level based on selection or campaign.

        Priority order:
            1. Specific level_id selected
            2. First level in campaign
            3. Default start level from registry
        """
        level_registry = self.services.get_global("level_registry")

        # Priority 1: Specific level selected
        if self.selected_level_id:
            level_config = level_registry.get(self.selected_level_id)
            if level_config:
                self._load_level(level_config)
                return

        # Priority 2: First level in campaign
        if self.campaign and len(self.campaign) > 0:
            self._load_level(self.campaign[0])
            return

        # Priority 3: Default start level
        start_level = level_registry.get_default_start()
        if start_level:
            self._load_level(start_level)

    def _load_level(self, level_config):
        """
        Load a specific level.

        Args:
            level_config: Level configuration object with name and path
        """
        DebugLogger.state(f"Starting level: {level_config.name}")
        self.level_manager.load(level_config.path)

        # Setup background from level data
        level_data = self.level_manager.get_current_level_data()
        if level_data:
            self._load_level_background(level_data)
            self._load_level_music(level_data)

    def _load_level_background(self, level_data):
        """
        Load background from level data.

        Args:
            level_data: Level data dict with optional 'background' section
        """
        default_layer = DEFAULT_BACKGROUND["layers"][0]

        if "background" in level_data:
            bg_config = {"layers": []}
            for layer in level_data["background"].get("layers", []):
                image = layer.get("image", default_layer["image"])
                if image and not image.startswith("assets/"):
                    image = MAPS_PATH + image

                merged = {
                    "image": image,
                    "scroll_speed": layer.get("scroll_speed", default_layer["scroll_speed"]),
                    "parallax": layer.get("parallax", default_layer["parallax"])
                }
                bg_config["layers"].append(merged)
        else:
            bg_config = DEFAULT_BACKGROUND

        self._setup_background(bg_config)

        is_snow_map = False
        base_image_path = bg_config["layers"][0]["image"]
        if "snow" in base_image_path.lower():
            is_snow_map = True

        DebugLogger.init(f"[BG Check] Path: {base_image_path}, Is Snow?: {is_snow_map}")

        if self.bg_manager.layer_count > 0 and is_snow_map:
            base_layer = self.bg_manager.get_layer(0)

            rock_images = [
                "assets/images/maps/rock_1.png",
                "assets/images/maps/rock_2.png",
                "assets/images/maps/rock_3.png",
                "assets/images/maps/rock_4.png",
                "assets/images/maps/rock_5.png",
            ]
            if hasattr(base_layer, "random_scatter_objects"):
                base_layer.random_scatter_objects(
                    object_paths = rock_images,
                    count = 7,
                    min_distance = 200
                )

    def _load_level_music(self, level_data):
        """
        Load music from level data.

        Args:
            level_data: Level data dict with optional 'music' key (filename only)
        """
        sound_manager = self.services.get_global("sound_manager")
        music_file = level_data.get("music")

        if music_file:
            route = BGM_PATH + music_file
            pygame.mixer.music.load(route)
            volume = sound_manager.master_volume * sound_manager.bgm_volume
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loops=-1)
            sound_manager.current_bgm_id = music_file
        else:
            sound_manager.play_bgm("game_bgm", loop=-1)  # Default

    # ===========================================================
    # Update Loop
    # ===========================================================

    def update(self, dt: float):
        """
        Update all game systems.

        Update Flow:
            1. Update overlay animation (always)
            2. Check for pending game over delay
            3. Update stat reveal animation
            4. Check player death
            5. Handle game over / paused / level up states
            6. Run active gameplay updates

        Args:
            dt: Delta time in seconds
        """
        # --- Always Update ---
        self.overlay.update(dt)

        # --- Cutscene Update ---
        if self.cutscene_manager.is_playing:
            self.cutscene_manager.update(dt)
            # Still update visuals during cutscene
            self._update_background(dt)
            self.player.anim_manager.update(dt)
            self.ui.update(dt, self.input_manager.get_effective_mouse_pos())
            return

        # --- Game Over Delay ---
        # Wait before showing game over screen (lets player see final moments)
        if self._game_over_pending:
            self._game_over_delay_timer -= dt
            if self._game_over_delay_timer <= 0:
                self._game_over_pending = False
                self._show_game_over(victory=self._game_over_victory)
                return

        # --- Stat Reveal Animation ---
        # Reveal stats one-by-one after game over screen appears
        if self.game_over_shown and self._stat_reveal_queue:
            self._update_stat_reveal(dt)

        # --- Player Death Check ---
        if self._check_player_death():
            return

        # --- State-Based Updates ---
        if self.game_over_shown:
            self._update_ui_only(dt)
            return

        if self.state == SceneState.PAUSED:
            self._update_ui_only(dt)
            return

        if self.level_up_ui.is_active:
            if self.input_manager.context != "ui":
                self.input_manager.set_context("ui")
            self._update_ui_only(dt)
            return

        # --- Level Up Trigger Check ---
        if self._check_level_up():
            return

        # --- Ensure Correct Input Context ---
        if self.input_manager.context != "gameplay":
            self.input_manager.set_context("gameplay")

        # --- Active Gameplay ---
        self._update_gameplay(dt)

        ParticleEmitter.update_all(dt)

    def _check_player_death(self):
        """
        Check and handle player death.

        Returns:
            bool: True if player died and game over triggered
        """
        if not self.game_over_shown and not self._game_over_pending and self.player.death_state == LifecycleState.DEAD:
            if self.level_up_ui.is_active:
                self.level_up_ui.hide()
            # Start delayed game over sequence
            self._game_over_pending = True
            self._game_over_victory = False
            self._game_over_delay_timer = GAME_OVER_DELAY
            return True
        return False

    def _check_level_up(self):
        """
        Check and handle player level up.

        Returns:
            bool: True if level up triggered
        """
        if self.player.level > self.last_player_level:
            if self.player.death_state == LifecycleState.ALIVE:
                DebugLogger.state(
                    f"Level up! {self.last_player_level} -> {self.player.level}"
                )
                self.input_manager.set_context("ui")
                self.level_up_ui.show()
                self.last_player_level = self.player.level

                sound_manager = self.services.get_global("sound_manager")
                sound_manager.stop_all_bfx()
                sound_manager.play_bfx("level_up")
                return True
            else:
                # Player died while leveling - update tracker only
                self.last_player_level = self.player.level
        return False

    def _update_ui_only(self, dt):
        """
        Update only UI (for paused/game over states).

        Args:
            dt: Delta time in seconds
        """
        mouse_pos = self.input_manager.get_effective_mouse_pos()
        self.ui.update(dt, mouse_pos)

    def _update_gameplay(self, dt):
        """
        Update active gameplay systems.

        Args:
            dt: Delta time in seconds
        """
        # Track play time
        get_session_stats().add_time(dt)

        # Update screen shake
        self.draw_manager.update_shake(dt)

        # Background parallax
        player_pos = (self.player.virtual_pos.x, self.player.virtual_pos.y)
        self._update_background(dt, player_pos)

        # Core systems
        self.player.update(dt)
        self.spawn_manager.update(dt)
        self.bullet_manager.update(dt)
        self.hazard_manager.update(dt)
        self.level_manager.update(dt)
        self.effects_manager.update(dt)

        # Collision detection
        self.collision_manager.update()
        self.collision_manager.detect()

        # Entity cleanup
        self.spawn_manager.cleanup()
        self.hazard_manager.cleanup()

        # UI update
        mouse_pos = self.input_manager.get_effective_mouse_pos()
        self.ui.update(dt, mouse_pos)

    # ===========================================================
    # Rendering
    # ===========================================================

    def draw(self, draw_manager):
        """
        Render all game elements.

        Draw Order:
            1. Player
            2. Enemies (via spawn_manager)
            3. Bullets
            4. Effects (pulse, flashes, etc.)
            5. Particles
            6. Overlay (dark tint for pause/game over)
            7. UI elements (includes level_up when active)
            8. Debug overlays (if enabled)

        Args:
            draw_manager: DrawManager for queuing draws
        """
        # Game entities
        self.player.draw(draw_manager)
        self.spawn_manager.draw()
        self.bullet_manager.draw(draw_manager)
        self.hazard_manager.draw()

        # Screen effects
        self.effects_manager.draw(draw_manager)

        ParticleEmitter.render_all(draw_manager)

        # Overlay (between game and UI)
        self.overlay.draw(draw_manager)

        # UI layers (includes level_up screen when active)
        self.ui.draw(draw_manager)

        # Cutscene overlays (text, etc)
        self.cutscene_manager.draw(draw_manager)

        # Debug overlays
        if Debug.HITBOX_VISIBLE:
            self.collision_manager.draw_debug(draw_manager)

    # ===========================================================
    # Event Handling
    # ===========================================================

    def handle_event(self, event):
        """
        Handle input events.

        Args:
            event: pygame event object
        """
        # UI event handling (includes level_up when active)
        action = self.ui.handle_event(event)
        self._handle_ui_action(action)

    def _handle_ui_action(self, action):
        """
        Handle UI button actions.

        Args:
            action: Action string from UI button
        """
        if action is None:
            return

        # Let level_up handle upgrade actions
        if self.level_up_ui.handle_action(action):
            return

        if action == "resume":
            self.scene_manager.resume_active_scene()
        elif action in ("quit", "return_to_menu"):
            self.scene_manager.set_scene("MainMenu", transition=FadeTransition(0.5))

    # ===========================================================
    # Game Events
    # ===========================================================

    def _on_level_complete(self):
        """
        Handle level completion.

        Starts delayed game over sequence with victory flag.
        """
        if not self.game_over_shown and not self._game_over_pending:
            # Start delay before showing game over
            self._game_over_pending = True
            self._game_over_victory = True
            self._game_over_delay_timer = GAME_OVER_DELAY

            DebugLogger.state(
                f"Level complete - game over in {GAME_OVER_DELAY}s",
                category="game"
            )

    def _on_enemy_died(self, event):
        """
        Handle enemy death event.

        Args:
            event: EnemyDiedEvent instance
        """
        get_session_stats().add_kill()
        get_session_stats().add_score(10)

        sound_manager = self.services.get_global("sound_manager")
        sound_manager.play_bfx("enemy_destroy")

        if get_session_stats().score > 0 and get_session_stats().score % 100 == 0:
            score_sound = ["score_sound1", "score_sound2", "score_sound3"]
            sound_manager.play_random_bfx(score_sound)

    def _on_screen_shake(self, event):
        """Handle screen shake event."""
        self.draw_manager.trigger_shake(event.intensity, event.duration)

    # ===========================================================
    # Game Over System
    # ===========================================================

    def _show_game_over(self, victory: bool):
        """
        Show game over overlay with animated stats.

        Flow:
            1. Set game over flag
            2. Start overlay fade
            3. Play game over music
            4. Update title text
            5. Prepare stats for reveal animation
            6. Show game over screen

        Args:
            victory: True for victory, False for defeat
        """
        self.game_over_shown = True

        # Start overlay fade (slower for dramatic effect)
        self.overlay.fade_in(speed=GAME_OVER_FADE_SPEED)

        # Audio transition
        sound_manager = self.services.get_global("sound_manager")
        if victory:
            sound_manager.play_bgm("game_clear", -1)
        else:
            sound_manager.play_bgm("game_over", -1)

        # Update title based on outcome
        self._update_game_over_title(victory)

        # Prepare stats for animated reveal
        self._prepare_stat_reveal()

        # Show the game over screen
        self.ui.show_screen("game_over", modal=True)

        # Enable keyboard navigation for game over UI
        self.input_manager.set_context("ui")

        DebugLogger.state(f"Game over shown (victory={victory})", category="game")

    def _update_game_over_title(self, victory: bool):
        """
        Update game over title based on outcome.

        Args:
            victory: True for victory, False for defeat
        """
        title_elem = self.ui.find_element_by_id("game_over", "title_label")
        if title_elem:
            if victory:
                title_elem.text = "MISSION ACCOMPLISHED"
                title_elem.text_color = (100, 255, 100)
            else:
                title_elem.text = "GAME OVER"
                title_elem.text_color = (255, 100, 100)
            title_elem.mark_dirty()

    def _prepare_stat_reveal(self):
        """
        Prepare stats for one-by-one reveal animation.

        Caches stat values and hides all stat labels initially.
        Stats will be revealed by _update_stat_reveal().
        """
        stats = get_session_stats()

        # Cache the final text values for each stat
        minutes = int(stats.run_time // 60)
        seconds = int(stats.run_time % 60)

        self._stat_values = {
            'score_label': f"Score: {stats.score}",
            'kills_label': f"Enemies Killed: {stats.enemies_killed}",
            'items_label': f"Items Collected: {stats.items_collected}",
            'time_label': f"Time: {minutes}:{seconds:02d}"
        }

        # Queue for reveal order
        self._stat_reveal_queue = [
            'score_label',
            'kills_label',
            'items_label',
            'time_label'
        ]

        # Reset reveal timer
        self._stat_reveal_timer = 0.0

        # Hide all stats initially (they'll appear one by one)
        for label_id in self._stat_values:
            elem = self.ui.find_element_by_id("game_over", label_id)
            if elem:
                elem.text = ""
                elem.mark_dirty()

    def _update_stat_reveal(self, dt):
        """
        Update stat reveal animation.

        Reveals one stat at a time based on timer interval.

        Args:
            dt: Delta time in seconds
        """
        self._stat_reveal_timer += dt

        # Check if it's time to reveal next stat
        if self._stat_reveal_timer >= STAT_REVEAL_DELAY:
            self._stat_reveal_timer = 0.0

            # Get next stat to reveal
            if self._stat_reveal_queue:
                label_id = self._stat_reveal_queue.pop(0)
                elem = self.ui.find_element_by_id("game_over", label_id)

                if elem and label_id in self._stat_values:
                    # Reveal the stat
                    elem.text = self._stat_values[label_id]
                    elem.mark_dirty()

                    DebugLogger.state(
                        f"Revealed stat: {label_id}",
                        category="game"
                    )