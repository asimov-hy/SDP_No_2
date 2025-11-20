"""
level_manager.py
----------------
Lightweight coordinator for stage-based level progression.

Architecture
------------
Delegates to specialized subsystems:
- StageLoader: Level data and stage management
- WaveScheduler: Wave spawning and timing

Responsibilities
----------------
- Coordinate subsystem updates
- Handle stage transitions
- Provide unified API for game scene
"""

from src.core.debug.debug_logger import DebugLogger
from src.systems.level.stage_loader import StageLoader
from src.systems.level.wave_scheduler import WaveScheduler


class LevelManager:
    """
    Lightweight coordinator for stage-based level progression.

    Delegates heavy lifting to StageLoader and WaveScheduler.
    """

    def __init__(self, spawn_manager, player_ref=None):
        """
        Initialize level manager and subsystems.

        Args:
            spawn_manager: SpawnManager instance for entity creation
            player_ref: Player entity reference for targeting
        """
        DebugLogger.init_entry("LevelManager Initialized")

        if player_ref is None:
            DebugLogger.warn(
                "[LevelManager] No player_ref provided - homing enemies will default to center targeting",
                category="level"
            )

        # Initialize subsystems
        self.stage_loader = StageLoader(spawn_manager)
        self.wave_scheduler = WaveScheduler(spawn_manager, player_ref)

        # Callback
        self.on_level_complete = None

    # ===========================================================
    # Loading
    # ===========================================================

    def load(self, level_path: str):
        """
        Load level and initialize first stage.

        Args:
            level_path: Path to level JSON file
        """
        if not level_path or not isinstance(level_path, str):
            DebugLogger.warn(
                f"[LevelManager] Invalid level_path: {level_path}",
                category="level"
            )
            return

        self.stage_loader.load(level_path)

        if not self.stage_loader.stages:
            DebugLogger.warn(
                f"[LevelManager] No stages loaded from {level_path}",
                category="level"
            )
            return

        self._load_stage(0)

    def _load_stage(self, stage_idx: int):
        """
        Load specific stage into subsystems.

        Args:
            stage_idx: Stage index to load
        """
        if stage_idx >= len(self.stage_loader.stages):
            self.stage_loader.active = False
            DebugLogger.system("Level complete - all stages finished", category="level")
            return

        stage = self.stage_loader.stages[stage_idx]
        stage_name = stage.get("name", f"Stage {stage_idx + 1}")

        DebugLogger.section(
            f"[ STAGE {stage_idx + 1}/{len(self.stage_loader.stages)} START ]: {stage_name}"
        )

        # Parse and load waves
        waves = self.stage_loader.parse_timeline(stage)
        self.wave_scheduler.load_waves(waves)

        # Load trigger
        self.stage_loader.load_trigger(stage)

        # Enable enemy tracking if needed
        if self.stage_loader.exit_trigger == "all_waves_cleared":
            self.wave_scheduler.enable_wave_clear_tracking()

        # Reset stage timer
        self.stage_loader.stage_timer = 0.0

        # Log stage info
        DebugLogger.init_sub(f"Waves: {len(waves)}, Events: 0")
        DebugLogger.init_sub(f"Exit Trigger: {self.stage_loader.exit_trigger}")
        DebugLogger.init_sub(f"Timer Reset → {self.stage_loader.stage_timer:.2f}s")
        DebugLogger.section("─" * 59 + "\n", only_title=True)

    # ===========================================================
    # Update Loop
    # ===========================================================

    def update(self, dt: float):
        """
        Update all subsystems.

        Args:
            dt: Delta time in seconds
        """
        if not self.stage_loader.active:
            return

        # Update timer
        self.stage_loader.update_timer(dt)

        # Update wave spawning
        self.wave_scheduler.update(dt, self.stage_loader.stage_timer)

        # Check stage completion
        if self._should_check_trigger():
            if self._check_trigger():
                self._next_stage()

    def _should_check_trigger(self) -> bool:
        """Determine if trigger should be evaluated."""
        waves_complete = self.wave_scheduler.is_waves_complete()
        return self.stage_loader.should_check_trigger(waves_complete)

    def _check_trigger(self) -> bool:
        """Check if stage completion trigger is satisfied."""
        waves_complete = self.wave_scheduler.is_waves_complete()
        remaining_enemies = self.wave_scheduler.get_remaining_enemies()
        return self.stage_loader.check_trigger(waves_complete, remaining_enemies)

    # ===========================================================
    # Stage Transitions
    # ===========================================================

    def _next_stage(self):
        """Advance to next stage or complete level."""
        if self.stage_loader.has_next_stage():
            self.stage_loader.advance_stage()
            self._load_stage(self.stage_loader.current_stage_idx)
        else:
            # Level complete
            self.stage_loader.active = False
            DebugLogger.system("Level complete", category="level")

            if self.on_level_complete:
                self.on_level_complete()

    # ===========================================================
    # Properties (for backward compatibility)
    # ===========================================================

    @property
    def active(self) -> bool:
        """Check if level is active."""
        return self.stage_loader.active

    @property
    def stage_timer(self) -> float:
        """Get current stage timer."""
        return self.stage_loader.stage_timer

    @property
    def current_stage_idx(self) -> int:
        """Get current stage index."""
        return self.stage_loader.current_stage_idx