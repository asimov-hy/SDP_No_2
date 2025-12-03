"""
boss_attack_base.py
-------------------
Base class for boss attacks. Each attack controls:
- Gun part behavior (rotation, shooting)
- Boss movement during attack
- Attack duration and timing
"""

import math
import pygame


class BossAttack:
    """
    Base class for all boss attacks.

    Lifecycle: start() → update(dt) each frame → finish()

    Subclasses override:
        - duration: How long attack lasts
        - _on_start(): Setup
        - _on_update(dt): Per-frame logic
        - _on_finish(): Cleanup
        - get_movement_override(): Control boss movement
    """

    def __init__(self, boss, bullet_manager):
        self.boss = boss
        self.bullet_manager = bullet_manager

        self.is_active = False
        self.timer = 0.0
        self.duration = 1.0  # Override in subclass

    @property
    def parts(self):
        """All boss gun parts."""
        return self.boss.parts

    @property
    def player_ref(self):
        return self.boss.player_ref

    # === Lifecycle ===

    def start(self):
        """Begin attack."""
        self.is_active = True
        self.timer = 0.0
        self._on_start()

    def update(self, dt):
        """Called each frame while active."""
        if not self.is_active:
            return

        self.timer += dt
        self._on_update(dt)

        if self.timer >= self.duration:
            self.finish()

    def finish(self):
        """End attack."""
        self.is_active = False
        self._on_finish()

    # === Override these ===

    def _on_start(self):
        pass

    def _on_update(self, dt):
        pass

    def _on_finish(self):
        pass

    def get_movement_override(self):
        """
        Return (vel_x, vel_y) to override boss movement.
        Return None for default movement.
        """
        return None

    # === Helpers ===

    def angle_to_player(self, from_pos) -> float:
        """Angle from position to player in degrees."""
        if not self.player_ref:
            return 180
        dx = self.player_ref.pos.x - from_pos.x
        dy = self.player_ref.pos.y - from_pos.y
        return math.degrees(math.atan2(dy, dx))