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
- JSON: {"phases": [{"waves": [...], "events": [...]}]}
"""

import os
from src.core.services.config_manager import load_config
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_state import EntityCategory
from src.systems.level.pattern_registry import PatternRegistry


class LevelManager:
    """
    Phase-based level coordinator.

    Handles multiphase levels_config with waves, events, and conditional triggers.
    Backward compatible with single-phase legacy format.
    """

    def __init__(self, spawn_manager, player_ref=None):
        """
        Initialize level manager.

        Args:
            spawn_manager: SpawnManager instance for entity creation
            level_data: Either:
                - str: Path to JSON level file
                - list: Legacy wave config [{"spawn_time": ...}]
                - dict: Full level config {"phases": [...]}
        """
        DebugLogger.init_entry("LevelManager Initialized")

        self.spawner = spawn_manager
        self.player = player_ref
        self.spawner.on_entity_destroyed = self._on_entity_destroyed

        # State
        self.data = None
        self.phases = []
        self.current_phase_idx = 0
        self.phase_timer = 0.0
        self._waiting_for_clear = False
        self._remaining_enemies = 0
        self.active = False

        self.waves = []
        self.wave_idx = 0
        self.events = []
        self.event_idx = 0
        self.exit_trigger = None
        self._trigger_func = lambda: False

        # Callback
        self.on_stage_complete = None

        # Deferred spawning state
        self._deferred_spawns = []  # Queue of (category, type_name, x, y, params)
        self._spawns_per_frame = 15  # Configurable threshold

    # ===========================================================
    # Data Loading
    # ===========================================================

    def load(self, level_path: str):
        """Load level config and initialize first phase."""

        self.data = self._load_level_data(level_path)
        self.phases = self.data.get("phases", [])

        # Full reset
        self.current_phase_idx = 0
        self.phase_timer = 0.0
        self._waiting_for_clear = False
        self._remaining_enemies = 0
        self.active = True

        if not self.phases:
            DebugLogger.warn("No phases in level")
            return

        self._load_phase(0)

    def _load_level_data(self, level_data):
        """
        Load and normalize level config from various sources.

        Returns:
            dict: Normalized level config with "phases" array
        """
        # Case 1: JSON or Python file path
        if isinstance(level_data, str):
            data = load_config(level_data, {"phases": []})
            DebugLogger.init_sub(f"Level Loaded: {os.path.basename(level_data)}")
            DebugLogger.warn(f"Loaded data keys: {list(data.keys())}")
            DebugLogger.warn(f"Phases count: {len(data.get('phases', []))}")
            DebugLogger.warn(f"Raw loaded data: {data}")
            DebugLogger.warn(f"Phases from data: {data.get('phases', 'KEY NOT FOUND')}")
            return data

        # Case 2: Already a dict
        if isinstance(level_data, dict):
            return level_data

        DebugLogger.warn(f"Invalid level_data type: {type(level_data)}")
        return {"phases": []}

    # ===========================================================
    # Phase Management
    # ===========================================================

    def _load_phase(self, phase_idx):
        """
        Load wave and event config for a specific phase.

        Args:
            phase_idx (int): Index in self.phases array
        """
        if phase_idx >= len(self.phases):
            self.active = False
            DebugLogger.system("Level complete - all phases finished")
            return

        phase = self.phases[phase_idx]
        phase_name = phase.get("name", phase.get("id", f"phase_{phase_idx}"))

        DebugLogger.section(f"[ PHASE {phase_idx + 1}/{len(self.phases)} START ]: {phase_name}")

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

        # Detailed initialization sublines
        DebugLogger.init_sub(f"Waves: {len(self.waves)}, Events: {len(self.events)}")
        DebugLogger.init_sub(f"Exit Trigger: {self.exit_trigger}")
        DebugLogger.init_sub(f"Timer Reset → {self.phase_timer:.2f}s")
        DebugLogger.section("─" * 59 + "\n", only_title=True)

        self._trigger_func = self._compile_trigger(self.exit_trigger)

    def _compile_trigger(self, trigger):
        """Return callable that checks completion"""

        # Time-based
        if trigger == "duration":
            duration = self.phases[self.current_phase_idx].get("duration", float('inf'))
            return lambda: self.phase_timer >= duration

        # Event-driven wave clear
        if trigger == "all_waves_cleared":
            self._waiting_for_clear = True
            self._remaining_enemies = 0  # Will be counted on spawn
            return lambda: (self.wave_idx >= len(self.waves) and
                            self._remaining_enemies <= 0)

        # Polling-based (legacy fallback)
        if trigger == "enemy_cleared":
            return lambda: not self._has_enemies_alive()

        # Complex triggers
        if isinstance(trigger, dict):
            return lambda: self._evaluate_complex_trigger(trigger)

        # Fallback
        DebugLogger.warn(f"Unknown trigger type: {trigger}")
        return lambda: False

    def _next_phase(self):
        """Advance to the next phase."""
        self.current_phase_idx += 1

        if self.current_phase_idx < len(self.phases):
            self._load_phase(self.current_phase_idx)
        else:
            # Stage fully complete
            self.active = False
            DebugLogger.system("Stage complete")

            if self.on_stage_complete:
                self.on_stage_complete()

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

        if not hasattr(self, 'waves'):
            return

        self._process_deferred_spawns()

        self.phase_timer += dt

        # Only check waves if any remain
        if self.wave_idx < len(self.waves):
            self._update_waves()

        # Only check events if any remain
        if self.event_idx < len(self.events):
            self._update_events()

        # Only check trigger if conditions met
        if self._should_check_trigger():
            if self._trigger_func():
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
        """
        # Determine entity type (enemy or item)
        if "enemy" in wave:
            category = "enemy"
            entity_type = wave.get("enemy", "straight")
            entity_params = wave.get("enemy_params", {})
        elif "pickup" in wave:
            category = "pickup"
            entity_type = wave.get("pickup", "health")
            entity_params = wave.get("item_params", {})
        else:
            DebugLogger.warn("Wave missing 'enemy' or 'item' key")
            return

        self._lazy_import_entity(category, entity_type)

        count = wave.get("count", 1)
        pattern = wave.get("pattern", "line")

        # Get spawn positions from pattern
        positions = self._calculate_positions(wave)

        # === PRE-COMPUTE: Once per wave (Strategy 1) ===
        spawn_edge = wave.get("spawn_edge") or wave.get("pattern_config", {}).get("edge")
        base_params = entity_params.copy()

        # Check if this is a homing enemy
        movement_config = wave.get("movement", {})
        is_homing = category == "enemy" and movement_config.get("type", "").startswith("homing")

        if is_homing:
            base_params["player_ref"] = self.player

        # Check if all enemies share the same direction (not position-dependent)
        needs_per_position_calc = (
                category == "enemy" and
                movement_config.get("type") == "straight" and
                movement_config.get("target") in ("center", "player")
        )

        # Pre-calculate shared movement for uniform direction waves
        if category == "enemy" and not needs_per_position_calc and positions:
            movement_params = self._calculate_movement(positions[0][0], positions[0][1], wave)
            base_params.update(movement_params)

        # === STRATEGY 3: Deferred spawning for large waves ===
        if len(positions) > self._spawns_per_frame:
            # Queue spawns for gradual processing
            for x, y in positions:
                spawn_params = base_params.copy()

                # Only recalculate if position-dependent
                if needs_per_position_calc:
                    movement_params = self._calculate_movement(x, y, wave)
                    spawn_params.update(movement_params)

                spawn_kwargs = {}
                if spawn_params.get("direction") is None and spawn_edge:
                    spawn_kwargs["spawn_edge"] = spawn_edge

                # Queue instead of spawning
                self._deferred_spawns.append((
                    category, entity_type, x, y,
                    {**spawn_kwargs, **spawn_params}
                ))

            DebugLogger.state(
                f"Queued {len(positions)} spawns (deferred) | Pattern: {pattern}",
                category="stage"
            )
        else:
            # Small wave - spawn immediately
            spawned = 0
            for x, y in positions:
                spawn_params = base_params.copy()

                # Only recalculate if position-dependent
                if needs_per_position_calc:
                    movement_params = self._calculate_movement(x, y, wave)
                    spawn_params.update(movement_params)

                # Add spawn_edge only if needed
                if spawn_params.get("direction") is None and spawn_edge:
                    spawn_params["spawn_edge"] = spawn_edge

                entity = self.spawner.spawn(
                    category, entity_type, x, y,
                    **spawn_params
                )

                if entity:
                    spawned += 1

            # Only track enemies for wave clear conditions
            if category == "enemy" and self._waiting_for_clear:
                self._remaining_enemies += spawned

            DebugLogger.state(
                f"Wave: {entity_type} x{count} | Pattern: {pattern}",
                category="stage"
            )

    # ===========================================================
    # Position Calculation (Unified Spawn System)
    # ===========================================================

    def _calculate_positions(self, wave):
        """
        Unified position calculation for three spawn modes.

        Auto-detects mode based on keys present in wave dict.

        Args:
            wave (dict): Wave configuration

        Returns:
            list[(float, float)]: Spawn positions
        """
        # Mode A: Direct spawn
        if "x" in wave and "y" in wave:
            count = wave.get("count", 1)
            return [(wave["x"], wave["y"])] * count

        # Mode B: Edge spawn
        if "spawn_edge" in wave:
            return self._positions_from_edge(wave)

        # Mode C: Pattern spawn
        if "pattern" in wave:
            return self._positions_from_pattern(wave)

        # Fallback
        DebugLogger.warn("Wave has no position config (x/y, spawn_edge, or pattern)")
        return [(640, -100)]

    def _positions_from_edge(self, wave):
        """
        Generate positions along edge with pixel-perfect control.

        Args:
            wave (dict): Must contain "spawn_edge", optional:
                - spawn_position: 0.0-1.0 (default 0.5)
                - spawn_position_random: variance range (default 0.0)
                - spawn_offset_x: absolute x offset (default 0)
                - spawn_offset_y: absolute y offset (default -100)
                - count: number of entities (default 1)

        Returns:
            list[(float, float)]: Calculated positions
        """
        import random

        edge = wave["spawn_edge"]
        position = wave.get("spawn_position", 0.5)
        random_range = wave.get("spawn_position_random", 0.0)
        offset_x = wave.get("spawn_offset_x", 0)
        offset_y = wave.get("spawn_offset_y", -100)
        count = wave.get("count", 1)

        width = getattr(self.spawner.display, "game_width", 1280)
        height = getattr(self.spawner.display, "game_height", 720)

        positions = []
        for _ in range(count):
            # Apply randomness to normalized position
            pos = position + random.uniform(-random_range, random_range)
            pos = max(0.0, min(1.0, pos))  # Clamp to [0, 1]

            # Convert to absolute coordinates based on edge
            if edge == "top":
                x = pos * width + offset_x
                y = offset_y
            elif edge == "bottom":
                x = pos * width + offset_x
                y = height + offset_y
            elif edge == "left":
                x = offset_x
                y = pos * height + offset_y
            elif edge == "right":
                x = width + offset_x
                y = pos * height + offset_y
            else:
                DebugLogger.warn(f"Unknown spawn_edge: {edge}")
                x, y = width / 2, -100

            positions.append((x, y))

        return positions

    def _positions_from_pattern(self, wave):
        """
        Generate positions using pattern registry.

        Args:
            wave (dict): Must contain "pattern", optional:
                - count: number of entities
                - pattern_config: dict passed to pattern function

        Returns:
            list[(float, float)]: Pattern-generated positions
        """
        pattern_name = wave["pattern"]
        count = wave.get("count", 1)
        pattern_config = wave.get("pattern_config", {})

        width = getattr(self.spawner.display, "game_width", 1280)
        height = getattr(self.spawner.display, "game_height", 720)

        positions = PatternRegistry.get_positions(
            pattern_name,
            count,
            width,
            height,
            pattern_config
        )

        return positions

    def _calculate_movement(self, x, y, wave):
        """Generate movement parameters based on movement config"""
        movement = wave.get("movement", {})
        move_type = movement.get("type", "straight")
        target = movement.get("target", "auto")

        if move_type == "straight":
            if target == "auto":
                return {
                    "direction": None
                }
            elif target == "center":
                direction = self._direction_to_center(x, y)
            elif target == "player":
                direction = self._direction_to_player(x, y)
            else:
                direction = (0, 1)  # Default down
            return {"direction": direction}

        elif move_type == "homing_continuous":
            return {
                "homing": True,
                "turn_rate": movement.get("params", {}).get("turn_rate", 180)
            }

        elif move_type == "homing_snapshot":
            return {
                "homing": "snapshot",
                "lock_delay": movement.get("params", {}).get("lock_delay", 0.5)
            }

        elif move_type == "stationary":
            return {"direction": (0, 0)}

        # Default fallback
        return {"direction": (0, 1)}

    def _direction_to_center(self, x, y):
        """Calculate direction to screen center"""
        import pygame

        width = getattr(self.spawner.display, "game_width", 1280)
        height = getattr(self.spawner.display, "game_height", 720)

        center_x, center_y = width / 2, height / 2
        dx, dy = center_x - x, center_y - y

        # Use pygame's fast C-level normalization
        vec = pygame.Vector2(dx, dy)
        if vec.length_squared() > 0:
            vec.normalize_ip()  # In-place, no allocation
            return (vec.x, vec.y)
        return (0, 1)

    def _direction_to_player(self, x, y):
        """Snapshot player position and calculate direction"""
        import pygame

        if not self.player:
            return (0, 1)

        dx, dy = self.player.pos.x - x, self.player.pos.y - y

        # Use pygame's fast C-level normalization
        vec = pygame.Vector2(dx, dy)
        if vec.length_squared() > 0:
            vec.normalize_ip()  # In-place, no allocation
            return (vec.x, vec.y)
        return (0, 1)

    def _on_entity_destroyed(self, entity):
        """Called by SpawnManager when entity dies"""
        if not self._waiting_for_clear or not self.active:
            return

        if entity.category == EntityCategory.ENEMY:
            self._remaining_enemies -= 1

            if self._remaining_enemies == 0 and self.wave_idx >= len(self.waves):
                self._waiting_for_clear = False
                self._next_phase()

    # ===========================================================
    # Event System (Dummy Handlers)
    # ===========================================================

    def _trigger_event(self, event):
        """
        Execute a scripted event.

        Args:
            event (dict): Event configuration
                {
                    "type": "music" | "dialogue" | "spawn_hazard",
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
            "spawn_hazard": self._event_spawn_hazard,
            "environment": self._event_environment,
        }
        return handlers.get(event_type)

    # Event handlers (dummy implementations with hooks for future systems)

    def _event_music(self, params):
        pass

    def _event_dialogue(self, params):
        pass

    def _event_spawn_hazard(self, params):
        pass

    def _event_environment(self, params):
        pass

    # ===========================================================
    # Trigger Evaluation (Phase Completion)
    # ===========================================================

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
        """Check if any ENEMY category entities_animation exist."""
        return any(
            getattr(e, "category", None) == EntityCategory.ENEMY
            for e in self.spawner.entities
        )

    def _has_category_alive(self, category):
        """Check if specific category entities_animation exist."""
        return any(
            getattr(e, "category", None) == category
            for e in self.spawner.entities
        )

    def _has_boss_alive(self, boss_id):
        """Check if specific boss entity exists."""
        # Requires boss entities_animation to have "boss_id" attribute
        return any(
            getattr(e, "boss_id", None) == boss_id
            for e in self.spawner.entities
        )

    def _should_check_trigger(self):
        """Only check trigger when waves are done or time-based."""
        trigger = self.exit_trigger

        if trigger == "duration":
            return True

        if trigger in ("all_waves_cleared", "enemy_cleared"):
            return self.wave_idx >= len(self.waves)

        # Complex triggers always check (they handle their own conditions)
        if isinstance(trigger, dict):
            return True

        return False

    def _lazy_import_entity(self, category, type_name):
        """
        Import entity module only when first needed.
        Triggers auto registration through __init_subclass__.
        """
        try:
            if category == "enemy":
                module_path = f"src.entities.enemies.enemy_{type_name}"
            elif category == "projectile":
                module_path = f"src.entities.bullets.bullet_{type_name}"
            elif category == "pickup":
                module_path = f"src.entities.items.item_{type_name}"
            else:
                return

            __import__(module_path)

        except Exception as e:
            from src.core.debug.debug_logger import DebugLogger
            DebugLogger.warn(
                f"[LazyLoad] Failed to import {category}:{type_name} ({e})"
            )

    def _process_deferred_spawns(self):
        """Process queued spawns gradually (called from update)."""
        if not self._deferred_spawns:
            return

        # Spawn batch this frame
        batch_size = min(self._spawns_per_frame, len(self._deferred_spawns))
        spawned = 0

        for _ in range(batch_size):
            category, entity_type, x, y, params = self._deferred_spawns.pop(0)
            entity = self.spawner.spawn(category, entity_type, x, y, **params)

            if entity:
                spawned += 1
                # Track enemies for wave clear
                if category == "enemy" and self._waiting_for_clear:
                    self._remaining_enemies += 1
