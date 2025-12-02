"""
boss_attack_base.py
-------------------
Base class for all boss part attacks.
"""

import math
import pygame


class BossAttack:
    """
    Abstract base for boss weapon attacks.

    Lifecycle:
        start() → update(dt) loop → finish  ()

    Subclasses override:
        - _on_start(): Setup attack state
        - _on_update(dt): Per-frame logic, return True when done
        - _on_finish(): Cleanup
    """

    def __init__(self, part, boss, bullet_manager, draw_manager):
        """
        Args:
            part: BossPart this attack belongs to
            boss: Parent EnemyBoss (for player_ref, position)
            bullet_manager: For spawning projectiles
            draw_manager: For visual effects (lasers, beams)
        """
        self.part = part
        self.boss = boss
        self.bullet_manager = bullet_manager
        self.draw_manager = draw_manager

        self.is_active = False
        self.timer = 0.0

    @property
    def player_ref(self):
        return self.boss.player_ref

    @property
    def part_pos(self):
        """Current world position of the part."""
        return self.part.pos.copy()

    def start(self):
        """Begin attack sequence."""
        if not self.part.active:
            return False

        self.is_active = True
        self.timer = 0.0
        self._on_start()
        return True

    def update(self, dt):
        """Update attack state. Called each frame while active."""
        if not self.is_active:
            return

        # Part destroyed mid-attack
        if not self.part.active:
            self.finish()
            return

        self.timer += dt

        if self._on_update(dt):
            self.finish()

    def finish(self):
        """End attack and cleanup."""
        self.is_active = False
        self._on_finish()

    # --- Override these ---

    def _on_start(self):
        """Setup attack state."""
        pass

    def _on_update(self, dt) -> bool:
        """
        Per-frame logic.

        Returns:
            True when attack is complete
        """
        return True

    def _on_finish(self):
        """Cleanup after attack ends."""
        pass

    # --- Debug ---

    def get_active_effects(self) -> list:
        """
        Override to return list of active effect names for debugging.
        Example: ["tracking", "aim_laser", "beam"]
        """
        return []

    # --- Utility methods ---

    def angle_to_player(self) -> float:
        """Get angle from part to player in degrees."""
        if not self.player_ref:
            return 270  # Default: aim down

        dx = self.player_ref.pos.x - self.part.pos.x
        dy = self.player_ref.pos.y - self.part.pos.y
        return math.degrees(math.atan2(dy, dx))

    def direction_to_player(self) -> pygame.Vector2:
        """Get normalized direction vector to player."""
        if not self.player_ref:
            return pygame.Vector2(0, 1)

        direction = self.player_ref.pos - self.part.pos
        if direction.length() > 0:
            direction.normalize_ip()
        return direction