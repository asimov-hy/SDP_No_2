"""
boss_attacks.py
---------------
Base class and concrete attack implementations.
"""

import math
import pygame

from src.core.services.event_manager import get_events, ScreenShakeEvent
from src.core.runtime.game_settings import Layers
from src.entities.environments.hazard_mine import TimedMine

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
        self.warn_time = 1.0       # Visible pause before charge
        self.rotate_time = 0.3    # Off-screen rotation
        self.track_time = 0.8     # Off-screen player tracking
        self.cooldown_time = 1.0
        self.charge_speed = 1000
        self.return_speed = 100
        self.screen_height = 720

        self.total_charges = 4
        self.duration = 15.0

        # Mine trail config
        self.mine_interval = 0.1
        self.mine_timer = 0.0

        # State
        self.phase = "warn"
        self.phase_timer = 0.0
        self.charge_count = 0
        self.going_down = True
        self.bottom_y = 0
        self.top_y = 0

        # Warning zone visual
        self.show_warning = False
        self.warning_alpha = 0

    def _on_start(self):
        self.phase = "warn"
        self.phase_timer = 0.0
        self.charge_count = 0
        self.going_down = True
        self.boss.entrance_complete = True
        self.mine_timer = 0.0

        half_height = self.boss.rect.height // 2
        self.bottom_y = self.screen_height + half_height
        self.top_y = -half_height

    def _on_update(self, dt):
        self.phase_timer += dt

        # Phase: Warn (on-screen, visible pause before charge)
        if self.phase == "warn":
            if self.phase_timer >= self.warn_time:
                self._next_phase("charge")
            return

        # Phase: Charge (move off-screen, drop mines)
        if self.phase == "charge":
            # Drop mines at interval
            self.mine_timer += dt
            if self.mine_timer >= self.mine_interval:
                self.mine_timer = 0.0
                self._spawn_mine()

            if self.going_down:
                self.boss.pos.y += self.charge_speed * dt
                if self.boss.pos.y >= self.bottom_y:
                    self.boss.pos.y = self.bottom_y
                    self._next_phase("rotate")
            else:
                self.boss.pos.y -= self.charge_speed * dt
                if self.boss.pos.y <= self.top_y:
                    self.boss.pos.y = self.top_y
                    self._next_phase("rotate")
            return

        # Phase: Rotate (off-screen, just wait)
        if self.phase == "rotate":
            if self.phase_timer >= self.rotate_time:
                if self.charge_count >= self.total_charges:
                    self._next_phase("cooldown")
                else:
                    self._next_phase("track")
            return

        # Phase: Cooldown (brief pause after charges complete)
        if self.phase == "cooldown":
            if self.phase_timer >= self.cooldown_time:
                self._next_phase("return")
            return

        # Phase: Track (off-screen, follow player X)
        if self.phase == "track":
            if self.player_ref:
                self.boss.pos.x = self.player_ref.pos.x
            if self.phase_timer >= self.track_time:
                self._next_phase("warn")
            return

        # Phase: Return home
        if self.phase == "return":
            self.boss.body_rotation = 0
            direction = self.boss.home_pos - self.boss.pos
            dist = direction.length()
            if dist < 10:
                self.boss.pos.xy = self.boss.home_pos.xy
                self.finish()
            else:
                direction.normalize_ip()
                self.boss.pos += direction * self.return_speed * dt

    def _next_phase(self, phase):
        self.phase = phase
        self.phase_timer = 0.0

        # One-time actions on phase entry
        if phase == "warn":
            get_events().dispatch(ScreenShakeEvent(intensity=3.0, duration=self.warn_time + 0.5))
            self.show_warning = True
            self.warning_alpha = 0

        elif phase == "charge":
            self.show_warning = False
            get_events().dispatch(ScreenShakeEvent(intensity=8.0, duration=2.0))

        # One-time actions on phase entry
        if phase == "rotate":
            self.going_down = not self.going_down
            self.boss.body_rotation = 0 if self.going_down else 180
            self.boss.sync_parts_to_body()
            self.charge_count += 1

    def _spawn_mine(self):
        """Drop a mine at boss position."""
        if not self.boss.hazard_manager:
            return

        # Only spawn if on screen
        if 0 < self.boss.pos.y < self.screen_height:
            self.boss.hazard_manager.spawn(
                TimedMine,
                self.boss.pos.x,
                self.boss.pos.y
            )

    def _on_finish(self):
        self.phase = "idle"
        self.boss.body_rotation = 0

    def get_movement_override(self):
        return (0, 0)

    def draw_warning(self, draw_manager):
        """Draw vertical danger zone during warn phase."""
        if not self.show_warning:
            return

        # Pulsing alpha
        pulse = abs(math.sin(self.phase_timer * 6))  # Fast pulse
        self.warning_alpha = int(40 + 60 * pulse)  # 40-100 alpha range

        # Vertical stripe at boss X, full screen height
        width = self.boss.rect.width + 40  # Slightly wider than boss
        x = int(self.boss.pos.x - width // 2)

        surf = pygame.Surface((width, self.screen_height), pygame.SRCALPHA)
        surf.fill((255, 0, 0, self.warning_alpha))

        rect = surf.get_rect(topleft=(x, 0))
        draw_manager.queue_draw(surf, rect, layer=Layers.BACKGROUND + 1)
