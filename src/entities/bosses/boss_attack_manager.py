"""
boss_attack_manager.py
----------------------
Manages boss attack state machine and attack selection.
"""

import random
from src.entities.bosses.boss_attacks import TraceAttack, SprayAttack


class BossAttackManager:
    """
    State machine: IDLE (cooldown) → random attack → IDLE

    Cooldown decreases as boss health drops.
    """

    def __init__(self, boss, bullet_manager):
        self.boss = boss
        self.bullet_manager = bullet_manager

        # State
        self.state = "IDLE"
        self.timer = 0.0
        self.current_attack = None

        # Available attacks
        self.attacks = {
            "TRACE": TraceAttack(boss, bullet_manager),
            "SPRAY": SprayAttack(boss, bullet_manager),
        }

    def _get_cooldown(self):
        """Cooldown shortens as health decreases."""
        hp_ratio = self.boss.health / self.boss.max_health
        # 3.0s at full HP → 1.0s at low HP
        return 1.0 + (2.0 * hp_ratio)

    def update(self, dt):
        """Update state machine."""
        self.timer += dt

        if self.state == "IDLE":
            self._update_idle(dt)

            if self.timer >= self._get_cooldown():
                self._start_random_attack()

        elif self.state == "ATTACKING":
            self.current_attack.update(dt)

            if not self.current_attack.is_active:
                self.state = "IDLE"
                self.timer = 0.0
                self.current_attack = None

    def _update_idle(self, dt):
        """Guns ease back to pointing down."""
        for part in self.boss.parts.values():
            if not part.active or getattr(part, 'is_static', False):
                continue

            # Ease angle toward 0 (base_angle handles down direction)
            part.angle *= 0.95
            if part._base_image:
                final_angle = part.base_angle + part.angle
                import pygame
                part.image = pygame.transform.rotate(part._base_image, -final_angle)
                part.rect = part.image.get_rect(center=(int(part.pos.x), int(part.pos.y)))

    def _start_random_attack(self):
        """Pick and start a random attack."""
        attack_name = random.choice(list(self.attacks.keys()))
        self.current_attack = self.attacks[attack_name]
        self.current_attack.start()
        self.state = "ATTACKING"
        self.timer = 0.0

    def get_movement_override(self):
        """Get movement override from current attack."""
        if self.current_attack and self.current_attack.is_active:
            return self.current_attack.get_movement_override()
        return None