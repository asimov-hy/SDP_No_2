"""
wave_scheduler.py
-----------------
Manages wave timing, spawning, and position calculation.

Responsibilities
----------------
- Schedule and trigger waves based on timeline
- Calculate spawn positions (edge, pattern, direct)
- Parse movement configurations
- Handle deferred spawning for large waves
- Track enemy counts for wave clear conditions
"""

import pygame
import random
from src.core.debug.debug_logger import DebugLogger
from src.entities.entity_types import EntityCategory
from src.systems.level.pattern_registry import PatternRegistry
from src.entities.entity_state import LifecycleState


class WaveScheduler:
    """Handles wave spawning, timing, and position calculation."""

    def __init__(self, spawn_manager, player_ref=None):
        """
        Initialize wave scheduler.

        Args:
            spawn_manager: SpawnManager for entity creation
            player_ref: Player entity reference for homing/targeting
        """
        self.spawner = spawn_manager
        self.player = player_ref

        # Wave state
        self.waves = []
        self.wave_idx = 0

        # Deferred spawning
        self._deferred_spawns = []
        self._spawns_per_frame = 15

        # Wave clear tracking
        self._waiting_for_clear = False
        self._remaining_enemies = 0

        # Callback for entity death
        self.spawner.on_entity_destroyed = self._on_entity_destroyed

        self._imported_entities = set()

    # ===========================================================
    # Wave Loading
    # ===========================================================

    def load_waves(self, waves: list):
        """
        Load waves for current stage.

        Args:
            waves: List of wave dicts with "time" field
        """
        self.waves = waves
        self.wave_idx = 0

    def enable_wave_clear_tracking(self):
        """Enable tracking enemies for all_waves_cleared trigger."""
        self._waiting_for_clear = True
        self._remaining_enemies = 0

    # ===========================================================
    # Update
    # ===========================================================

    def update(self, dt: float, stage_timer: float):
        """
        Update wave spawning and process deferred spawns.

        Args:
            dt: Delta time
            stage_timer: Current stage time
        """
        # Process deferred spawns from previous frames
        self._process_deferred_spawns()

        # Check if any waves should trigger
        while (self.wave_idx < len(self.waves) and
               stage_timer >= self.waves[self.wave_idx].get("time", 0)):
            self._trigger_wave(self.waves[self.wave_idx])
            self.wave_idx += 1

    # ===========================================================
    # Wave State
    # ===========================================================

    def is_waves_complete(self) -> bool:
        """Check if all waves have been triggered."""
        return self.wave_idx >= len(self.waves)

    def get_remaining_enemies(self) -> int:
        """Get count of tracked enemies still alive."""
        return self._remaining_enemies

    # ===========================================================
    # Wave Spawning
    # ===========================================================

    def _trigger_wave(self, wave: dict):
        """
        Spawn entities for a wave.

        Args:
            wave: Wave configuration dict
        """
        # VALIDATION: Check wave structure
        if not isinstance(wave, dict):
            DebugLogger.warn(
                f"[WaveScheduler] Invalid wave type: {type(wave)}",
                category="level"
            )
            return

        # Determine entity type (enemy or pickup)
        if "enemy" in wave:
            category = "enemy"
            entity_type = wave.get("enemy", "straight")
            entity_params = wave.get("enemy_params", {})
        elif "pickup" in wave:
            category = "pickup"
            entity_type = wave.get("pickup", "health")
            entity_params = wave.get("item_params", {})
        else:
            DebugLogger.warn(
                "[WaveScheduler] Wave missing 'enemy' or 'pickup' key",
                category="level"
            )
            return

        # VALIDATION: Required parameters
        if not entity_type:
            DebugLogger.warn(
                "[WaveScheduler] Wave has empty entity_type",
                category="level"
            )
            return

        count = wave.get("count", 1)
        if count <= 0:
            DebugLogger.warn(
                f"[WaveScheduler] Invalid count: {count}",
                category="level"
            )
            return

        # Try lazy import
        self._lazy_import_entity(category, entity_type)

        pattern = wave.get("pattern", "line")

        # Calculate spawn positions
        positions = self._calculate_positions(wave)

        # VALIDATION: Check positions
        if not positions:
            DebugLogger.warn(
                f"[WaveScheduler] No valid positions for wave {entity_type} (pattern: {pattern})",
                category="level"
            )
            return

        # Pre-compute wave parameters
        spawn_edge = wave.get("spawn_edge") or wave.get("pattern_config", {}).get("edge")
        base_params = entity_params.copy()

        # Parse movement configuration
        if category == "enemy":
            needs_position_calc, movement_params = self._parse_movement_config(wave)

            # Inject player reference for homing
            if "homing" in movement_params:
                movement_params["player_ref"] = self.player

            # Pre-compute if uniform direction
            if not needs_position_calc:
                base_params.update(movement_params)
        else:
            needs_position_calc = False
            movement_params = {}

        # Deferred spawning for large waves
        if len(positions) > self._spawns_per_frame:
            for x, y in positions:
                spawn_params = base_params.copy()

                if needs_position_calc:
                    direction_params = self._calculate_position_dependent_direction(
                        x, y, movement_params.get("target")
                    )
                    spawn_params.update(direction_params)

                spawn_kwargs = {}
                if spawn_edge:
                    if spawn_params.get("direction") is None or spawn_params.get("homing") == "snapshot_axis":
                        spawn_kwargs["spawn_edge"] = spawn_edge

                self._deferred_spawns.append((
                    category, entity_type, x, y,
                    {**spawn_kwargs, **spawn_params}
                ))

            DebugLogger.state(
                f"Queued {len(positions)} spawns (deferred) | Pattern: {pattern}",
                category="level"
            )
        else:
            # Immediate spawning for small waves
            spawned = 0
            failed = 0

            for x, y in positions:
                # VALIDATION: Coordinate types
                if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                    DebugLogger.warn(
                        f"[WaveScheduler] Invalid position: ({x}, {y})",
                        category="level"
                    )
                    failed += 1
                    continue

                spawn_params = base_params.copy()

                if needs_position_calc:
                    direction_params = self._calculate_position_dependent_direction(
                        x, y, movement_params.get("target")
                    )
                    spawn_params.update(direction_params)

                if spawn_edge:
                    if spawn_params.get("direction") is None or spawn_params.get("homing") == "snapshot_axis":
                        spawn_params["spawn_edge"] = spawn_edge

                entity = self.spawner.spawn(category, entity_type, x, y, **spawn_params)

                if entity:
                    spawned += 1
                else:
                    failed += 1

            # Track enemies for wave clear
            if category == "enemy" and self._waiting_for_clear:
                self._remaining_enemies += spawned

            # Report results
            if failed > 0:
                DebugLogger.warn(
                    f"[WaveScheduler] Wave spawn incomplete: {spawned} succeeded, {failed} failed",
                    category="level"
                )

            DebugLogger.state(
                f"Wave: {entity_type} x{spawned}/{count} | Pattern: {pattern}",
                category="level"
            )

    # ===========================================================
    # Position Calculation
    # ===========================================================

    def _calculate_positions(self, wave: dict) -> list:
        """
        Calculate spawn positions from wave config.

        Args:
            wave: Wave dict with position config

        Returns:
            list: [(x, y), ...] spawn positions
        """
        # Mode A: Direct coordinates
        if "x" in wave and "y" in wave:
            count = wave.get("count", 1)
            x, y = wave["x"], wave["y"]

            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                DebugLogger.warn(
                    f"[WaveScheduler] Invalid x/y coordinates: ({x}, {y})",
                    category="level"
                )
                return []

            return [(float(x), float(y))] * count

        # Mode B: Edge spawn
        if "spawn_edge" in wave:
            edge = wave.get("spawn_edge")
            if edge not in ["top", "bottom", "left", "right"]:
                DebugLogger.warn(
                    f"[WaveScheduler] Invalid spawn_edge: '{edge}'",
                    category="level"
                )
                return []
            return self._positions_from_edge(wave)

        # Mode C: Pattern spawn
        if "pattern" in wave:
            return self._positions_from_pattern(wave)

        DebugLogger.warn(
            "[WaveScheduler] Wave has no position config (x/y, spawn_edge, or pattern)",
            category="level"
        )
        return []

    def _positions_from_edge(self, wave: dict) -> list:
        """Generate positions along screen edge."""

        edge = wave["spawn_edge"]
        position = wave.get("spawn_position", 0.5)
        random_range = wave.get("spawn_position_random", 0.0)
        offset_x = wave.get("spawn_offset_x", 0)
        offset_y = wave.get("spawn_offset_y", -100)
        count = wave.get("count", 1)

        # FIXED: Safe display access
        if self.spawner.display:
            width = getattr(self.spawner.display, "game_width", 1280)
            height = getattr(self.spawner.display, "game_height", 720)
        else:
            width, height = 1280, 720

        positions = []
        for _ in range(count):
            pos = position + random.uniform(-random_range, random_range)
            pos = max(0.0, min(1.0, pos))

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
                x, y = width / 2, -100

            positions.append((x, y))

        return positions

    def _positions_from_pattern(self, wave: dict) -> list:
        """Generate positions using pattern registry."""
        pattern_name = wave["pattern"]
        count = wave.get("count", 1)
        pattern_config = wave.get("pattern_config", {})

        # FIXED: Safe display access
        if self.spawner.display:
            width = getattr(self.spawner.display, "game_width", 1280)
            height = getattr(self.spawner.display, "game_height", 720)
        else:
            width, height = 1280, 720

        try:
            positions = PatternRegistry.get_positions(
                pattern_name, count, width, height, pattern_config
            )
            return positions
        except KeyError as e:
            # Pattern not found
            DebugLogger.warn(
                f"[WaveScheduler] Pattern '{pattern_name}' not registered: {e}",
                category="level"
            )
            return []
        except (ValueError, TypeError) as e:
            # Invalid parameters
            DebugLogger.warn(
                f"[WaveScheduler] Pattern '{pattern_name}' invalid config: {e}",
                category="level"
            )
            return []
        except Exception as e:
            # Other errors
            DebugLogger.warn(
                f"[WaveScheduler] Pattern '{pattern_name}' failed: {e}",
                category="level"
            )
            return []

    # ===========================================================
    # Movement Parsing
    # ===========================================================

    def _parse_movement_config(self, wave: dict):
        """
        Parse movement config from wave.

        Returns:
            tuple: (needs_position_calc: bool, params: dict)
        """
        movement = wave.get("movement", {})
        move_type = movement.get("type", "straight")
        target = movement.get("target", "auto")

        if move_type == "homing_continuous":
            return False, {
                "homing": True,
                "turn_rate": movement.get("params", {}).get("turn_rate", 180)
            }
        elif move_type == "homing_snapshot":
            return False, {
                "homing": "snapshot",
                "lock_delay": movement.get("params", {}).get("lock_delay", 0.5)
            }
        elif move_type == "homing_snapshot_axis":
            return False, {
                "homing": "snapshot_axis",
                "lock_delay": movement.get("params", {}).get("lock_delay", 0.5)
            }
        elif move_type == "straight":
            if target == "auto":
                return False, {"direction": None}
            elif target in ("center", "player"):
                return True, {"target": target}
            else:
                return False, {"direction": (0, 1)}
        elif move_type == "stationary":
            return False, {"direction": (0, 0)}

        return False, {"direction": (0, 1)}

    def _calculate_position_dependent_direction(self, x: float, y: float, target: str) -> dict:
        """Calculate direction based on position and target."""
        if target == "center":
            return {"direction": self._direction_to_center(x, y)}
        elif target == "player":
            return {"direction": self._direction_to_player(x, y)}
        else:
            # FIXED: Warn on unknown target
            if target:  # Only warn if target was specified
                DebugLogger.warn(
                    f"[WaveScheduler] Unknown movement target '{target}' - using default down",
                    category="level"
                )
            return {"direction": (0, 1)}

    def _direction_to_center(self, x: float, y: float) -> tuple:
        """Calculate normalized direction to screen center."""
        width = getattr(self.spawner.display, "game_width", 1280)
        height = getattr(self.spawner.display, "game_height", 720)

        center_x, center_y = width / 2, height / 2
        dx, dy = center_x - x, center_y - y

        vec = pygame.Vector2(dx, dy)
        if vec.length_squared() > 0:
            vec.normalize_ip()
            return (vec.x, vec.y)
        return (0, 1)

    def _direction_to_player(self, x: float, y: float) -> tuple:
        """Calculate normalized direction to player."""
        # FIXED: Better handling when player unavailable
        if not self.player:
            DebugLogger.warn(
                "[WaveScheduler] Player reference missing - using center targeting fallback",
                category="level"
            )
            return self._direction_to_center(x, y)

        # FIXED: Check if player is dead
        if hasattr(self.player, 'death_state'):
            if self.player.death_state >= LifecycleState.DEAD:
                return self._direction_to_center(x, y)

        dx, dy = self.player.pos.x - x, self.player.pos.y - y

        vec = pygame.Vector2(dx, dy)
        if vec.length_squared() > 0:
            vec.normalize_ip()
            return (vec.x, vec.y)
        return (0, 1)

    # ===========================================================
    # Deferred Spawning
    # ===========================================================
    def _process_deferred_spawns(self):
        """Process queued spawns gradually."""
        if not self._deferred_spawns:
            return

        # FIXED: Add hard cap with emergency drain
        MAX_QUEUE_SIZE = 500
        queue_len = len(self._deferred_spawns)

        if queue_len > MAX_QUEUE_SIZE:
            DebugLogger.warn(
                f"[WaveScheduler] EMERGENCY DRAIN: Queue at {queue_len}, processing all at once",
                category="level"
            )
            # Emergency: drain entire queue
            batch_size = queue_len
        else:
            batch_size = min(self._spawns_per_frame, queue_len)

        # Warn if backing up
        if queue_len > 100:
            DebugLogger.warn(
                f"[WaveScheduler] Deferred spawn queue: {queue_len} pending",
                category="level"
            )

        spawned = 0
        failed = 0

        for _ in range(batch_size):
            category, entity_type, x, y, params = self._deferred_spawns.pop(0)
            entity = self.spawner.spawn(category, entity_type, x, y, **params)

            if entity:
                spawned += 1
                if category == "enemy" and self._waiting_for_clear:
                    self._remaining_enemies += 1
            else:
                failed += 1

        if failed > 0:
            DebugLogger.warn(
                f"[WaveScheduler] {failed}/{batch_size} deferred spawns failed this frame",
                category="level"
            )

    # ===========================================================
    # Enemy Tracking
    # ===========================================================

    def _on_entity_destroyed(self, entity):
        """Called by SpawnManager when entity dies."""
        if not self._waiting_for_clear:
            return

        # FIXED: Safe category check
        category = getattr(entity, 'category', None)
        if category == EntityCategory.ENEMY:
            self._remaining_enemies -= 1

    # ===========================================================
    # Utility
    # ===========================================================

    def _lazy_import_entity(self, category: str, type_name: str):
        """Import entity module to trigger registration."""

        key = (category, type_name)
        if key in self._imported_entities:
            return  # Already imported
        self._imported_entities.add(key)

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
            DebugLogger.warn(
                f"Failed to import {category}:{type_name} - {e}",
                category="level"
            )