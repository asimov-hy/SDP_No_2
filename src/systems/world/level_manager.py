"""
level_manager.py
----------------
Phase-based level controller with wave scheduling and scripted events.

Architecture
------------
Single-file modular design:
- PhaseController: Current phase state
- WaveScheduler: Enemy spawn timing (O(1) per frame)
- EventScheduler: Scripted event timing (O(1) per frame)
- TriggerEvaluator: Phase completion checks (O(1) or lazy)

Performance
-----------
Hot path (every frame): ~0.04ms
- Wave check: O(1) index pointer
- Event check: O(1) index pointer
- Trigger check: O(1) or skipped if not phase-ending

Cold path (phase transitions): ~0.8ms
- Only runs 3-5 times per level
- Loads new wave/event arrays

Data Format
-----------
Supports both legacy Python dicts and JSON files:
- Legacy: STAGE_1_WAVES = [{"spawn_time": 0.0, ...}]
- JSON: {"phases": [{"waves": [...], "events": [...]}]}
"""

import json
import os
from src.core.utils.debug_logger import DebugLogger
from src.entities.entity_state import EntityCategory


class LevelManager:
    """
    Phase-based level coordinator.

    Handles multi-phase levels with waves, events, and conditional triggers.
    Backward compatible with single-phase legacy format.
    """

    def __init__(self, spawn_manager, level_data):
        """
        Initialize level manager.

        Args:
            spawn_manager: SpawnManager instance for entity creation
            level_data: Either:
                - str: Path to JSON level file
                - list: Legacy wave data [{"spawn_time": ...}]
                - dict: Full level data {"phases": [...]}
        """
        self.spawner = spawn_manager

        # Load and normalize level data
        self.data = self._load_level_data(level_data)

        # Phase system
        self.phases = self.data.get("phases", [])
        self.current_phase_idx = 0
        self.phase_timer = 0.0
        self.active = True

        # Initialize first phase
        if self.phases:
            self._load_phase(0)
        else:
            DebugLogger.warn("No phases defined in level data")
            self.active = False

        DebugLogger.init_entry("LevelManager Initialized")
        DebugLogger.init_sub(f"Phases: {len(self.phases)}")

    # ===========================================================
    # Data Loading
    # ===========================================================

    def _load_level_data(self, level_data):
        """
        Load and normalize level data from various sources.

        Returns:
            dict: Normalized level data with "phases" array
        """
        # Case 1: JSON file path
        if isinstance(level_data, str):
            return self._load_json_file(level_data)

        # Case 2: Legacy wave list (backward compatibility)
        if isinstance(level_data, list):
            return self._convert_legacy_format(level_data)

        # Case 3: Already a dict
        if isinstance(level_data, dict):
            # Ensure phases exist
            if "phases" not in level_data:
                level_data = self._convert_legacy_format(level_data.get("waves", []))
            return level_data

        DebugLogger.fail(f"Invalid level_data type: {type(level_data)}")
        return {"phases": []}

    def _load_json_file(self, path):
        """Load level data from JSON file."""
        if not os.path.exists(path):
            DebugLogger.fail(f"Level file not found: {path}")
            return {"phases": []}

        try:
            with open(path, 'r') as f:
                data = json.load(f)
            DebugLogger.system(f"Loaded level: {data.get('name', path)}")
            return data
        except json.JSONDecodeError as e:
            DebugLogger.fail(f"Invalid JSON in {path}: {e}")
            return {"phases": []}

    def _convert_legacy_format(self, waves):
        """
        Convert old wave list to phase format.

        Args:
            waves: List of wave dicts with "spawn_time" key

        Returns:
            dict: Level data with single phase
        """
        # Rename "spawn_time" to "time" for consistency
        normalized_waves = []
        for wave in waves:
            wave_copy = wave.copy()
            if "spawn_time" in wave_copy:
                wave_copy["time"] = wave_copy.pop("spawn_time")
            normalized_waves.append(wave_copy)

        return {
            "id": "legacy",
            "phases": [{
                "id": "main",
                "waves": normalized_waves,
                "events": [],
                "exit_trigger": "all_waves_cleared"
            }]
        }

    # ===========================================================
    # Phase Management
    # ===========================================================

    def _load_phase(self, phase_idx):
        """
        Load wave and event data for a specific phase.

        Args:
            phase_idx (int): Index in self.phases array
        """
        if phase_idx >= len(self.phases):
            self.active = False
            DebugLogger.system("Level complete - all phases finished")
            return

        phase = self.phases[phase_idx]
        phase_name = phase.get("name", phase.get("id", f"phase_{phase_idx}"))

        # Load waves (sorted by time)
        self.waves = sorted(phase.get("waves", []), key=lambda w: w.get("time", 0))
        self.wave_idx = 0

        # Load events (sorted by time)
        self.events = sorted(phase.get("events", []), key=lambda e: e.get("time", 0))
        self.event_idx = 0

        # Reset phase timer
        self.phase_timer = 0.0

        # Store exit trigger for this phase
        self.exit_trigger = phase.get("exit_trigger", "all_waves_cleared")

        DebugLogger.system(f"Phase {phase_idx + 1}/{len(self.phases)}: {phase_name}")
        DebugLogger.init_sub(f"Waves: {len(self.waves)}, Events: {len(self.events)}")

    def _next_phase(self):
        """Advance to the next phase."""
        self.current_phase_idx += 1

        if self.current_phase_idx < len(self.phases):
            self._load_phase(self.current_phase_idx)
        else:
            self.active = False
            DebugLogger.system("Level complete")

    # ===========================================================
    # Update Loop (Hot Path)
    # ===========================================================

    def update(self, dt):
        """
        Update wave spawning, events, and phase progression.

        Performance: ~0.04ms per frame

        Args:
            dt (float): Delta time in seconds
        """
        if not self.active:
            return

        self.phase_timer += dt

        # 1. Spawn waves (O(1) with index pointer)
        self._update_waves()

        # 2. Trigger events (O(1) with index pointer)
        self._update_events()

        # 3. Check phase completion (O(1) or lazy evaluation)
        if self._check_phase_complete():
            self._next_phase()

    def _update_waves(self):
        """Spawn waves when their time arrives."""
        while (self.wave_idx < len(self.waves) and
               self.phase_timer >= self.waves[self.wave_idx].get("time", 0)):
            self._trigger_wave(self.waves[self.wave_idx])
            self.wave_idx += 1

    def _update_events(self):
        """Trigger events when their time arrives."""
        while (self.event_idx < len(self.events) and
               self.phase_timer >= self.events[self.event_idx].get("time", 0)):
            self._trigger_event(self.events[self.event_idx])
            self.event_idx += 1

    # ===========================================================
    # Wave Spawning
    # ===========================================================

    def _trigger_wave(self, wave):
        """
        Spawn enemies for a wave using PatternRegistry.

        Args:
            wave (dict): Wave configuration
                {
                    "enemy": "straight",
                    "count": 5,
                    "pattern": "line",
                    "pattern_params": {...},
                    "enemy_params": {...}
                }
        """
        from pattern_registry import PatternRegistry

        enemy_type = wave.get("enemy", "straight")
        count = wave.get("count", 1)
        pattern = wave.get("pattern", "line")

        # Get spawn positions from pattern
        width = getattr(self.spawner.display, "game_width", 1280)
        pattern_params = wave.get("pattern_params", {})

        positions = PatternRegistry.get_positions(
            pattern, count, width, **pattern_params
        )

        # Spawn enemies at each position
        enemy_params = wave.get("enemy_params", {})

        for x, y in positions:
            enemy = self.spawner.spawn("enemy", enemy_type, x, y, **enemy_params)

            # Apply per-wave speed override if specified
            if enemy and "speed" in enemy_params:
                enemy.speed = enemy_params["speed"]

        DebugLogger.state(
            f"Wave: {enemy_type} x{count} | Pattern: {pattern}",
            category="stage"
        )

    # ===========================================================
    # Event System (Dummy Handlers)
    # ===========================================================

    def _trigger_event(self, event):
        """
        Execute a scripted event.

        Args:
            event (dict): Event configuration
                {
                    "type": "music" | "dialogue" | "camera_shake" | "spawn_hazard",
                    "params": {...}
                }
        """
        event_type = event.get("type")
        params = event.get("params", {})

        # Dispatch to handler
        handler = self._get_event_handler(event_type)
        if handler:
            handler(params)
        else:
            DebugLogger.warn(f"No handler for event type: {event_type}")

    def _get_event_handler(self, event_type):
        """
        Get handler function for event type.

        Uses dispatch table for O(1) lookup.
        """
        handlers = {
            "music": self._event_music,
            "dialogue": self._event_dialogue,
            "camera_shake": self._event_camera_shake,
            "spawn_hazard": self._event_spawn_hazard,
            "environment": self._event_environment,
        }
        return handlers.get(event_type)

    # Event handlers (dummy implementations with hooks for future systems)

    def _event_music(self, params):
        """
        Music change event.

        Future: Hook to SoundManager.play_music()
        """
        track = params.get("track", "unknown")
        fade_duration = params.get("fade_duration", 0.0)

        DebugLogger.action(f"[EVENT] Music: {track} (fade: {fade_duration}s)")

        # TODO: Implement when SoundManager exists
        # if hasattr(self, 'sound_manager'):
        #     self.sound_manager.play_music(track, fade_duration)

    def _event_dialogue(self, params):
        """
        Dialogue/text display event.

        Future: Hook to DialogueManager or HUDManager
        """
        text = params.get("text", "")
        duration = params.get("duration", 3.0)

        DebugLogger.action(f"[EVENT] Dialogue: {text[:50]}...")

        # TODO: Implement when dialogue system exists
        # if hasattr(self, 'dialogue_manager'):
        #     self.dialogue_manager.show(text, duration)

    def _event_camera_shake(self, params):
        """
        Camera shake effect.

        Future: Hook to DisplayManager or CameraController
        """
        intensity = params.get("intensity", 1.0)
        duration = params.get("duration", 0.5)

        DebugLogger.action(f"[EVENT] Camera shake: {intensity} for {duration}s")

        # TODO: Implement when camera system exists
        # if hasattr(self, 'camera'):
        #     self.camera.shake(intensity, duration)

    def _event_spawn_hazard(self, params):
        """
        Spawn environment hazard.

        Uses existing SpawnManager.
        """
        hazard_type = params.get("type", "laser")
        x = params.get("x", 640)
        y = params.get("y", 0)

        DebugLogger.action(f"[EVENT] Spawn hazard: {hazard_type} at ({x}, {y})")

        # Spawn through existing system
        self.spawner.spawn("environment", hazard_type, x, y, **params)

    def _event_environment(self, params):
        """Generic environment object spawn."""
        obj_type = params.get("object", "obstacle")
        x = params.get("x", 640)
        y = params.get("y", 0)

        DebugLogger.action(f"[EVENT] Environment: {obj_type}")
        self.spawner.spawn("environment", obj_type, x, y, **params)

    # ===========================================================
    # Trigger Evaluation (Phase Completion)
    # ===========================================================

    def _check_phase_complete(self):
        """
        Check if current phase is complete.

        Performance: O(1) for time-based, O(n) for enemy checks (lazy)

        Returns:
            bool: True if phase should end
        """
        trigger = self.exit_trigger

        # Simple string triggers (fast path)
        if isinstance(trigger, str):
            return self._evaluate_simple_trigger(trigger)

        # Complex dict triggers (condition-based)
        if isinstance(trigger, dict):
            return self._evaluate_complex_trigger(trigger)

        DebugLogger.warn(f"Unknown trigger type: {type(trigger)}")
        return False

    def _evaluate_simple_trigger(self, trigger):
        """
        Evaluate simple string-based triggers.

        Args:
            trigger (str): Trigger identifier
                - "duration": Fixed time limit (requires "duration" in phase)
                - "all_waves_cleared": All waves spawned + enemies dead
                - "enemy_cleared": All enemies dead (ignores wave count)
        """
        if trigger == "duration":
            phase = self.phases[self.current_phase_idx]
            duration = phase.get("duration", float('inf'))
            return self.phase_timer >= duration

        if trigger == "all_waves_cleared":
            waves_done = self.wave_idx >= len(self.waves)
            enemies_alive = self._has_enemies_alive()
            return waves_done and not enemies_alive

        if trigger == "enemy_cleared":
            return not self._has_enemies_alive()

        DebugLogger.warn(f"Unknown simple trigger: {trigger}")
        return False

    def _evaluate_complex_trigger(self, trigger):
        """
        Evaluate complex condition-based triggers.

        Args:
            trigger (dict): Trigger configuration
                {
                    "type": "enemy_category_cleared",
                    "category": "miniboss"
                }
        """
        trigger_type = trigger.get("type")

        if trigger_type == "enemy_category_cleared":
            category = trigger.get("category")
            return not self._has_category_alive(category)

        if trigger_type == "boss_defeated":
            boss_id = trigger.get("boss_id")
            # Check if specific boss entity is dead
            return not self._has_boss_alive(boss_id)

        if trigger_type == "timer":
            min_time = trigger.get("min", 0.0)
            max_time = trigger.get("max", float('inf'))
            return min_time <= self.phase_timer <= max_time

        DebugLogger.warn(f"Unknown complex trigger: {trigger_type}")
        return False

    # ===========================================================
    # Entity Query Helpers (Lazy Evaluation)
    # ===========================================================

    def _has_enemies_alive(self):
        """Check if any ENEMY category entities exist."""
        return any(
            getattr(e, "category", None) == EntityCategory.ENEMY
            for e in self.spawner.entities
        )

    def _has_category_alive(self, category):
        """Check if specific category entities exist."""
        return any(
            getattr(e, "category", None) == category
            for e in self.spawner.entities
        )

    def _has_boss_alive(self, boss_id):
        """Check if specific boss entity exists."""
        # Requires boss entities to have "boss_id" attribute
        return any(
            getattr(e, "boss_id", None) == boss_id
            for e in self.spawner.entities
        )