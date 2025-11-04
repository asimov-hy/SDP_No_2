"""
stage_manager.py
----------------
Controls stage progression and predefined enemy waves.

Responsibilities
----------------
- Load predefined wave data per stage.
- Trigger waves based on stage timer.
- Simplify wave creation for designers.
"""

from src.core.utils.debug_logger import DebugLogger

class StageManager:
    """Handles stage timing, wave scheduling, and progression."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, spawner, stage_data):
        """
        Initialize the stage manager.

        Args:
            spawner: Reference to SpawnManager.
            stage_data (list[dict]): List of wave dictionaries for this stage.
        """
        self.spawner = spawner
        self.stage_data = sorted(stage_data, key=lambda w: w["spawn_time"])
        self.stage_timer = 0.0
        self.wave_index = 0
        self.stage_active = True

        DebugLogger.init("Initialized StageManager with predefined waves")

    # ===========================================================
    # Update Logic
    # ===========================================================
    def update(self, dt: float):
        """
        Update stage timer and trigger waves when scheduled.

        Args:
            dt (float): Delta time since last frame.
        """
        if not self.stage_active:
            return

        self.stage_timer += dt

        # Process scheduled waves
        while (self.wave_index < len(self.stage_data) and
               self.stage_timer >= self.stage_data[self.wave_index]["spawn_time"]):
            wave = self.stage_data[self.wave_index]
            self._trigger_wave(wave)
            self.wave_index += 1

        # End condition: all waves spawned and all enemies cleared
        if self.wave_index >= len(self.stage_data) and not self.spawner.enemies:
            self.stage_active = False
            DebugLogger.state("Stage complete — all waves cleared")

    # ===========================================================
    # Wave Triggering
    # ===========================================================
    def _trigger_wave(self, wave: dict):
        """
        Spawn all enemies for a specific wave.

        Args:
            wave (dict): Wave configuration dictionary.
        """
        pattern = wave.get("pattern", "line")
        count = wave.get("count", 1)
        enemy_type = wave.get("enemy_type", "basic")
        y_offset = wave.get("y_offset", -100)
        speed = wave.get("speed", None)

        width = self.spawner.display.get_window_size()[0] if self.spawner.display else 800

        DebugLogger.system(f"Triggering wave: {wave}")

        DebugLogger.system(f"Triggering wave {self.wave_index + 1}: {enemy_type} ×{count} ({pattern})")

        # Basic formation patterns
        if pattern == "line":
            spacing = width // (count + 1)
            for i in range(count):
                x = spacing * (i + 1)
                self.spawner.spawn_enemy(enemy_type, x, y_offset)

        elif pattern == "v":
            center_x = width // 2
            x_spacing = 120  # horizontal distance between enemies
            y_spacing = 40  # vertical spacing per row
            tip_depth = 120  # how deep the V goes

            for i in range(count):
                # offset index relative to center
                rel = i - (count - 1) / 2
                x = center_x + rel * x_spacing

                # Make the center enemy lowest (the tip of the V)
                y = y_offset + tip_depth - abs(rel) * y_spacing

                self.spawner.spawn_enemy(enemy_type, x, y)

        else:
            DebugLogger.warn(f"Unknown pattern: {pattern}")
