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
@attack(enabled=False)
class TraceAttack(BossAttack):
    """Track player and fire in bursts."""

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)

        # Tweakable timing parameters
        self.idle_start = 1.0  # Idle before bursts
        self.burst_time = 1.0  # Shooting duration per cycle
        self.pause_time = 1.0  # Pause between bursts
        self.burst_count = 5  # Number of burst cycles
        self.idle_end = 1.0  # Idle after bursts

        # Auto-calculate total duration
        self.cycle_time = self.burst_time + self.pause_time
        self.duration = self.idle_start + (self.cycle_time * self.burst_count) + self.idle_end

        self.fire_rate = 0.12
        self.bullet_speed = 450

    def _on_update(self, dt):
        # Phase 1: Idle start
        if self.timer < self.idle_start:
            return

        # Phase 2: Burst cycles
        burst_phase_time = self.timer - self.idle_start
        burst_phase_end = self.cycle_time * self.burst_count

        if burst_phase_time >= burst_phase_end:
            # Phase 3: Idle end
            return

        cycle_pos = burst_phase_time % self.cycle_time
        is_shooting = cycle_pos < self.burst_time

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

@attack(enabled=True)
class ChargeAttack(BossAttack):
    """Multi-phase charge attack with off-screen dives."""

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)

        # Config
        self.rev_up_time = 1.0
        self.pause_time = 1.0     # Tracks player
        self.warn_time = 0.5      # Locked, no tracking
        self.charge_speed = 1000
        self.return_speed = 100
        self.screen_height = 720

        self.total_charges = 4    # down, up, down, up

        self.duration = 15.0

        # State
        self.phase = "rev_up"
        self.phase_timer = 0.0
        self.charge_count = 0
        self.going_down = True    # First charge goes down
        self.bottom_y = 0
        self.top_y = 0

        # Rotation
        self.target_rotation = 0
        self.rotation_speed = 360

    def _on_start(self):
        self.phase = "rev_up"
        self.phase_timer = 0.0
        self.charge_count = 0
        self.going_down = True
        self.target_rotation = 0
        self.boss.entrance_complete = True

        half_height = self.boss.rect.height // 2
        self.bottom_y = self.screen_height + half_height
        self.top_y = -half_height

    def _on_update(self, dt):
        self.phase_timer += dt

        # Phase: Rev up
        if self.phase == "rev_up":
            if self.phase_timer >= self.rev_up_time:
                self._next_phase("charge")
            return

        # Phase: Charge (no rotation change during charge)
        if self.phase == "charge":
            if self.going_down:
                self.boss.pos.y += self.charge_speed * dt
                if self.boss.pos.y >= self.bottom_y:
                    self.boss.pos.y = self.bottom_y
                    self._charge_complete()
            else:
                self.boss.pos.y -= self.charge_speed * dt
                if self.boss.pos.y <= self.top_y:
                    self.boss.pos.y = self.top_y
                    self._charge_complete()
            return

        # Phase: Pause (tracks player) - snap rotation for next charge
        if self.phase == "pause_track":
            if self.player_ref:
                self.boss.pos.x = self.player_ref.pos.x
            # Snap once on phase entry (going_down hasn't flipped yet, so invert)
            new_rotation = 180 if self.going_down else 0
            self.boss.body_rotation = new_rotation

            if self.phase_timer >= self.pause_time:
                self._next_phase("warn")
            return

        # Phase: Warn (locked position)
        if self.phase == "warn":
            if self.phase_timer >= self.warn_time:
                self.going_down = not self.going_down  # Flip direction
                self._next_phase("charge")
            return

        # Phase: Final pause before return - snap to face down
        if self.phase == "pause_final":
            self.boss.body_rotation = 0  # Face down for return
            if self.phase_timer >= self.pause_time:
                self._next_phase("return")
            return

        # Phase: Return home
        if self.phase == "return":
            direction = self.boss.home_pos - self.boss.pos
            dist = direction.length()
            if dist < 10:
                self.boss.pos.xy = self.boss.home_pos.xy
                self.finish()
            else:
                direction.normalize_ip()
                self.boss.pos += direction * self.return_speed * dt

    def _update_rotation(self, dt):
        current = self.boss.body_rotation
        diff = self.target_rotation - current

        # Shortest path
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        max_step = self.rotation_speed * dt
        if abs(diff) < max_step:
            self.boss.body_rotation = self.target_rotation
        else:
            self.boss.body_rotation += max_step if diff > 0 else -max_step

    def _charge_complete(self):
        self.charge_count += 1
        if self.charge_count >= self.total_charges:
            self._next_phase("return")
        else:
            self._next_phase("pause_track")

    def _next_phase(self, phase):
        self.phase = phase
        self.phase_timer = 0.0

    def _on_finish(self):
        self.phase = "idle"
        self.boss.body_rotation = 0

    def get_movement_override(self):
        return (0, 0)