"""
boss_attack_manager.py
----------------------
Boss attack state machine.
"""

import random
import pygame

from src.entities.bosses.boss_attacks import ATTACK_REGISTRY


class BossAttackManager:
    """State machine: IDLE -> ATTACKING -> IDLE"""

    def __init__(self, boss, bullet_manager):
        self.boss = boss
        self.bullet_manager = bullet_manager

        self.state = "IDLE"
        self.timer = 0.0
        self.current_attack = None

        self.attacks = {
            name: cls(boss, bullet_manager) for name, cls in ATTACK_REGISTRY.items()
        }

    def _get_cooldown(self):
        hp_ratio = self.boss.health / self.boss.max_health
        return 1.0 + (2.0 * hp_ratio)

    def update(self, dt):
        self.timer += dt

        if self.state == "IDLE":
            self._update_idle(dt)
            if self.timer >= self._get_cooldown() and self.attacks:
                self._start_random_attack()

        elif self.state == "ATTACKING":
            self.current_attack.update(dt)
            if not self.current_attack.is_active:
                self.state = "IDLE"
                self.timer = 0.0
                self.current_attack = None

    def _update_idle(self, dt):
        for part in self.boss.parts.values():
            if not part.active or getattr(part, "is_static", False):
                continue
            part.angle *= 0.95
            if part._base_image:
                final_angle = part.base_angle + part.angle
                part.image = pygame.transform.rotate(part._base_image, -final_angle)
                part.rect = part.image.get_rect(
                    center=(int(part.pos.x), int(part.pos.y))
                )

    def _start_random_attack(self):
        attack_name = random.choice(list(self.attacks.keys()))
        self.current_attack = self.attacks[attack_name]
        self.current_attack.start()
        self.state = "ATTACKING"
        self.timer = 0.0

    def get_movement_override(self):
        if self.current_attack and self.current_attack.is_active:
            return self.current_attack.get_movement_override()
        return None

    def draw(self, draw_manager):
        """Draw attack visuals (warning zones, etc.)"""
        if self.current_attack and hasattr(self.current_attack, "draw_warning"):
            self.current_attack.draw_warning(draw_manager)
