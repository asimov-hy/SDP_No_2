"""
boss_attacks.py
---------------
Base class and concrete attack implementations.
"""

import math
import pygame

# =====================
# ATTACK REGISTRY
# =====================
ATTACK_REGISTRY = {}


def attack(enabled=True):
    """Decorator to register attacks. Set enabled=False to disable."""
    def decorator(cls):
        if enabled:
            ATTACK_REGISTRY[cls.__name__] = cls
        return cls
    return decorator


# =====================
# BASE CLASS
# =====================
class BossAttack:
    """
    Base class for boss attacks.
    Lifecycle: start() -> update(dt) -> finish()
    """

    def __init__(self, boss, bullet_manager):
        self.boss = boss
        self.bullet_manager = bullet_manager

        self.is_active = False
        self.timer = 0.0
        self.duration = 1.0

        # Movement override
        self.movement_type = None
        self.movement_speed = 0

        # Bullet overrides (None = use part defaults)
        self.fire_rate = None
        self.bullet_speed = None

        self._part_defaults = {}

    @property
    def parts(self):
        return self.boss.parts

    @property
    def player_ref(self):
        return self.boss.player_ref

    def start(self):
        self.is_active = True
        self.timer = 0.0
        self._apply_attack_config()
        self._on_start()

    def update(self, dt):
        if not self.is_active:
            return
        self.timer += dt
        self._on_update(dt)
        if self.timer >= self.duration:
            self.finish()

    def finish(self):
        self.is_active = False
        self._on_finish()
        self._restore_part_defaults()

    def _on_start(self):
        pass

    def _on_update(self, dt):
        pass

    def _on_finish(self):
        pass

    def get_movement_override(self):
        if self.movement_type == "strafe_left":
            return (-self.movement_speed, 0)
        elif self.movement_type == "strafe_right":
            return (self.movement_speed, 0)
        elif self.movement_type == "charge":
            return (0, self.movement_speed)
        elif self.movement_type == "retreat":
            return (0, -self.movement_speed)
        return None

    def _apply_attack_config(self):
        for name, part in self.parts.items():
            if getattr(part, 'is_static', False):
                continue
            self._part_defaults[name] = {
                'fire_rate': part.fire_rate,
                'bullet_speed': part.bullet_speed,
            }
            if self.fire_rate is not None:
                part.fire_rate = self.fire_rate
            if self.bullet_speed is not None:
                part.bullet_speed = self.bullet_speed

    def _restore_part_defaults(self):
        for name, defaults in self._part_defaults.items():
            if name in self.parts:
                part = self.parts[name]
                part.fire_rate = defaults['fire_rate']
                part.bullet_speed = defaults['bullet_speed']
        self._part_defaults.clear()


# =====================
# ATTACKS
# =====================
@attack(enabled=True)
class TraceAttack(BossAttack):
    """Track player and fire in bursts."""

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)
        self.duration = 12.0
        self.cycle_time = 4.0

        self.fire_rate = 0.12
        self.bullet_speed = 450

    def _on_update(self, dt):
        cycle_pos = self.timer % self.cycle_time
        is_shooting = cycle_pos < 2.0

        for part in self.parts.values():
            if not part.active or getattr(part, 'is_static', False):
                continue
            if self.player_ref:
                part.rotate_towards_player(self.player_ref, dt)
            if is_shooting and "mg" in part.name:
                part.update_shooting(dt, self.bullet_manager, spray_mode=False)


@attack(enabled=False)
class SprayAttack(BossAttack):
    """Sweep guns back and forth while firing."""

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)
        self.duration = 5.0

        self.movement_type = "strafe_left"
        self.movement_speed = 10

        self.fire_rate = 0.25
        self.bullet_speed = 300

    def _on_update(self, dt):
        for part in self.parts.values():
            if not part.active or getattr(part, 'is_static', False):
                continue
            part.spray_rotate(dt)
            if "mg" in part.name:
                part.update_shooting(dt, self.bullet_manager, spray_mode=True)