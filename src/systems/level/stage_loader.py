"""
stage_loader.py
---------------
Manages level data loading, stage progression, and trigger compilation.

Responsibilities
----------------
- Load and validate level JSON
- Parse timeline format into wave entries
- Manage current stage state
- Compile and evaluate stage completion triggers
"""

import os
from src.core.services.config_manager import load_config
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_types import EntityCategory


class StageLoader:
    """Handles level data loading and stage state management."""

    def __init__(self, spawn_manager):
        """
        Initialize stage loader.

        Args:
            spawn_manager: Reference to check entity states for triggers
        """
        self.spawn_manager = spawn_manager

        # Level data
        self.data = None
        self.stages = []

        # Current stage state
        self.current_stage_idx = 0
        self.stage_timer = 0.0
        self.active = False

        # Trigger state
        self.exit_trigger = None
        self._trigger_func = lambda: False

    # ===========================================================
    # Loading
    # ===========================================================

    def load(self, level_path: str):
        """
        Load level config from file or dict.

        Args:
            level_path: Path to level JSON or dict object
        """
        self.data = self._load_level_data(level_path)

        # VALIDATION: Ensure stages is a list
        stages_data = self.data.get("stages", [])
        if not isinstance(stages_data, list):
            DebugLogger.warn(
                f"[StageLoader] Invalid stages format: {type(stages_data)}. Expected list.",
                category="level"
            )
            self.stages = []
        else:
            self.stages = stages_data

        # Reset state
        self.current_stage_idx = 0
        self.stage_timer = 0.0
        self.active = True

        if not self.stages:
            DebugLogger.warn("[StageLoader] No stages in level", category="level")
            return

        DebugLogger.init_sub(f"Loaded {len(self.stages)} stage(s) from level")

    def _load_level_data(self, level_data):
        """
        Load and normalize level config from various sources.

        Args:
            level_data: File path (str) or dict

        Returns:
            dict: Normalized level config with "stages" array
        """
        # Case 1: JSON or Python file path
        if isinstance(level_data, str):
            data = load_config(level_data, {"stages": []})
            DebugLogger.init_sub(f"Level Loaded: {os.path.basename(level_data)}")
            return data

        # Case 2: Already a dict
        if isinstance(level_data, dict):
            return level_data

        DebugLogger.warn(
            f"[StageLoader] Invalid level_data type: {type(level_data)}",
            category="level"
        )
        return {"stages": []}

    # ===========================================================
    # Stage Access
    # ===========================================================

    def get_current_stage(self) -> dict:
        """
        Get current stage data.

        Returns:
            dict: Current stage or empty dict if invalid
        """
        if 0 <= self.current_stage_idx < len(self.stages):
            return self.stages[self.current_stage_idx]
        return {}

    def has_next_stage(self) -> bool:
        """Check if there's another stage after current."""
        return self.current_stage_idx + 1 < len(self.stages)

    def advance_stage(self):
        """Move to next stage."""
        self.current_stage_idx += 1
        self.stage_timer = 0.0

    # ===========================================================
    # Timeline Parsing
    # ===========================================================
    def parse_timeline(self, stage: dict) -> list:
        """
        Parse stage timeline into flat wave list.

        Args:
            stage: Stage dictionary with "timeline" key

        Returns:
            list: Wave entries with "time" field added
        """
        timeline_data = stage.get("timeline", {})

        # VALIDATION: Ensure timeline is a dict
        if not isinstance(timeline_data, dict):
            DebugLogger.warn(
                f"[StageLoader] Stage has invalid timeline format: {type(timeline_data)}",
                category="level"
            )
            return []

        waves = []

        # FIXED: Safe iteration with time validation
        for time_str in sorted(timeline_data.keys(), key=lambda x: float(x) if isinstance(x, (str, int, float)) else 0):
            spawns = timeline_data[time_str]

            # VALIDATION: Ensure spawns is a list
            if not isinstance(spawns, list):
                DebugLogger.warn(
                    f"[StageLoader] Timeline entry at {time_str} is not a list: {type(spawns)}",
                    category="level"
                )
                continue

            # FIXED: Validate time conversion
            try:
                time_float = float(time_str)
            except (ValueError, TypeError) as e:
                DebugLogger.warn(
                    f"[StageLoader] Invalid time format '{time_str}': {e}",
                    category="level"
                )
                continue

            for spawn in spawns:
                if not isinstance(spawn, dict):
                    DebugLogger.warn(
                        f"[StageLoader] Invalid spawn entry at time {time_str}",
                        category="level"
                    )
                    continue

                wave_entry = spawn.copy()
                wave_entry["time"] = time_float
                waves.append(wave_entry)

        return waves

    # ===========================================================
    # Timer
    # ===========================================================

    def update_timer(self, dt: float):
        """Update stage timer."""
        self.stage_timer += dt

    # ===========================================================
    # Trigger System
    # ===========================================================

    def load_trigger(self, stage: dict):
        """
        Compile trigger function for stage completion.

        Args:
            stage: Stage dict with "exit_trigger" key
        """
        self.exit_trigger = stage.get("exit_trigger", "all_waves_cleared")
        self._trigger_func = self._compile_trigger(self.exit_trigger)

    def _compile_trigger(self, trigger):
        """
        Compile trigger condition into callable.

        Args:
            trigger: Trigger config (string or dict)

        Returns:
            callable: Function that returns True when stage complete
        """
        # Time-based
        if trigger == "duration":
            duration = self.stages[self.current_stage_idx].get("duration", float('inf'))
            return lambda: self.stage_timer >= duration

        # Event-driven wave clear (requires external enemy count)
        if trigger == "all_waves_cleared":
            # This will be checked externally by level_manager
            return lambda: False  # Placeholder

        # Polling-based
        if trigger == "enemy_cleared":
            return lambda: not self._has_enemies_alive()

        # Complex triggers
        if isinstance(trigger, dict):
            return lambda: self._evaluate_complex_trigger(trigger)

        # Fallback
        DebugLogger.warn(
            f"[StageLoader] Unknown trigger type: {trigger}",
            category="level"
        )
        return lambda: False

    def should_check_trigger(self, waves_complete: bool) -> bool:
        """
        Determine if trigger should be evaluated this frame.

        Args:
            waves_complete: Whether all waves have been triggered

        Returns:
            bool: True if trigger should be checked
        """
        trigger = self.exit_trigger

        if trigger == "duration":
            return True

        if trigger in ("all_waves_cleared", "enemy_cleared"):
            return waves_complete

        # Complex triggers always check
        if isinstance(trigger, dict):
            return True

        return False

    def check_trigger(self, waves_complete: bool, remaining_enemies: int) -> bool:
        """
        Check if stage completion trigger is satisfied.

        Args:
            waves_complete: Whether all waves spawned
            remaining_enemies: Count of enemies alive

        Returns:
            bool: True if stage complete
        """
        # Special case: all_waves_cleared needs external state
        if self.exit_trigger == "all_waves_cleared":
            return waves_complete and remaining_enemies <= 0

        # All other triggers use compiled function
        return self._trigger_func()

    def _evaluate_complex_trigger(self, trigger: dict) -> bool:
        """
        Evaluate complex condition-based triggers.

        Args:
            trigger: Trigger configuration dict

        Returns:
            bool: True if condition met
        """
        trigger_type = trigger.get("type")

        if trigger_type == "enemy_category_cleared":
            category = trigger.get("category")
            return not self._has_category_alive(category)

        if trigger_type == "boss_defeated":
            boss_id = trigger.get("boss_id")
            return not self._has_boss_alive(boss_id)

        if trigger_type == "timer":
            min_time = trigger.get("min", 0.0)
            max_time = trigger.get("max", float('inf'))
            return min_time <= self.stage_timer <= max_time

        DebugLogger.warn(
            f"[StageLoader] Unknown complex trigger: {trigger_type}",
            category="level"
        )
        return False

    # ===========================================================
    # Entity Query Helpers
    # ===========================================================

    def _has_enemies_alive(self) -> bool:
        """Check if any ENEMY category entities exist."""
        return any(
            getattr(e, "category", None) == EntityCategory.ENEMY
            for e in self.spawn_manager.entities
        )

    def _has_category_alive(self, category) -> bool:
        """Check if specific category entities exist."""
        return any(
            getattr(e, "category", None) == category
            for e in self.spawn_manager.entities
        )

    def _has_boss_alive(self, boss_id) -> bool:
        """Check if specific boss entity exists."""
        return any(
            getattr(e, "boss_id", None) == boss_id
            for e in self.spawn_manager.entities
        )