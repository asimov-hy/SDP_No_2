"""
boss_attacks.py
---------------
Concrete attack implementations for boss.
"""

from src.entities.bosses.boss_attack_base import BossAttack


class TraceAttack(BossAttack):
    """
    Track player and fire in bursts.
    Pattern: 2s shoot → 2s pause × 3 cycles = 12s total
    """

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)
        self.duration = 12.0
        self.cycle_time = 4.0  # 2s shoot + 2s pause

    def _on_update(self, dt):
        cycle_pos = self.timer % self.cycle_time
        is_shooting = cycle_pos < 2.0

        for part in self.parts.values():
            if not part.active or getattr(part, 'is_static', False):
                continue

            # Track player
            if self.player_ref:
                part.rotate_towards_player(self.player_ref, dt)

            # Shoot during first half of cycle
            if is_shooting and "mg" in part.name:
                part.update_shooting(dt, self.bullet_manager, spray_mode=False)


class SprayAttack(BossAttack):
    """
    Sweep guns back and forth while firing continuously.
    Duration: 5 seconds
    """

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)
        self.duration = 5.0

    def _on_update(self, dt):
        for part in self.parts.values():
            if not part.active or getattr(part, 'is_static', False):
                continue

            # Sweep rotation
            part.spray_rotate(dt)

            # Continuous fire
            if "mg" in part.name:
                part.update_shooting(dt, self.bullet_manager, spray_mode=True)