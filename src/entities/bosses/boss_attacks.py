"""
boss_attacks.py
---------------
Base class and concrete attack implementations.
"""

import math
import random
import pygame

from src.core.services.event_manager import get_events, ScreenShakeEvent
from src.entities.bullets.bullet_bouncing import BouncingBullet
from src.core.runtime.game_settings import Display, Layers
from src.graphics.particles.particle_manager import DebrisEmitter
from src.entities.environments.hazard_mine import TimedMine
from src.audio.sound_manager import get_sound_manager

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

        # Movement config
        self.movement_type = (
            "idle"  # idle, chase, strafe_left, strafe_right, charge, retreat
        )
        self.movement_speed = 0
        self.bob_enabled = True  # Vertical bobbing

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
        """Return (vx, vy) or None for chase."""
        if self.movement_type == "chase":
            return None
        elif self.movement_type == "strafe_left":
            return (-self.movement_speed, 0)
        elif self.movement_type == "strafe_right":
            return (self.movement_speed, 0)
        elif self.movement_type == "charge":
            return (0, self.movement_speed)
        elif self.movement_type == "retreat":
            return (0, -self.movement_speed)
        return (0, 0)  # idle

    def _apply_attack_config(self):
        for name, part in self.parts.items():
            if getattr(part, "is_static", False):
                continue
            self._part_defaults[name] = {
                "fire_rate": part.fire_rate,
                "bullet_speed": part.bullet_speed,
            }
            if self.fire_rate is not None:
                part.fire_rate = self.fire_rate
            if self.bullet_speed is not None:
                part.bullet_speed = self.bullet_speed

    def _restore_part_defaults(self):
        for name, defaults in self._part_defaults.items():
            if name in self.parts:
                part = self.parts[name]
                part.fire_rate = defaults["fire_rate"]
                part.bullet_speed = defaults["bullet_speed"]
        self._part_defaults.clear()


# =====================
# ATTACKS
# =====================
@attack(enabled=True)
class TraceAttack(BossAttack):
    """Track player and fire in bursts."""

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)

        # Tweakable timing parameters
        self.idle_start = 1.0  # Idle before bursts
        self.burst_time = 0.7  # Shooting duration per cycle
        self.pause_time = 0.5  # Pause between bursts
        self.burst_count = 5  # Number of burst cycles
        self.idle_end = 0.5  # Idle after bursts

        # Auto-calculate total duration
        self.cycle_time = self.burst_time + self.pause_time
        self.duration = (
            self.idle_start + (self.cycle_time * self.burst_count) + self.idle_end
        )

        self.fire_rate = 0.05
        self.bullet_speed = 450

        self.movement_type = (
            "chase"  # idle, chase, strafe_left, strafe_right, charge, retreat
        )
        self.movement_speed = 50

    def _on_update(self, dt):
        # Phase 1: Idle start
        if self.timer < self.idle_start:
            return

        # Phase 2: Burst cycles
        burst_phase_time = self.timer - self.idle_start
        burst_phase_end = self.cycle_time * self.burst_count

        if burst_phase_time >= 0 and not getattr(self, "trace_sound_played", False):
            get_sound_manager().play_bfx_loop("boss_trace_player", loop=-1)
            self.trace_sound_played = True

        played_sound_current_frame = False

        if burst_phase_time >= burst_phase_end:
            if getattr(self, "motor_sound_played", False):
                get_sound_manager().stop_bfx("boss_trace_player")
                self.trace_sound_played = False
            # Phase 3: Idle end
            return

        cycle_pos = burst_phase_time % self.cycle_time
        is_shooting = cycle_pos < self.burst_time

        for part in self.parts.values():
            if not part.active or getattr(part, "is_static", False):
                continue
            if self.player_ref:
                part.rotate_towards_player(self.player_ref, dt)

            if is_shooting and "mg" in part.name:
                if part.update_shooting(dt, self.bullet_manager, spray_mode=False):
                    if not played_sound_current_frame:
                        get_sound_manager().play_bfx("boss_trace_fire")
                        played_sound_current_frame = True


@attack(enabled=True)
class SprayAttack(BossAttack):
    """Sweep guns back and forth while firing bouncing bullets."""

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)

        # Sweep config
        self.num_sweeps = 1  # Number of full back-and-forth sweeps
        self.sweep_speed = 60  # Degrees per second (overrides part default)
        self.angle_range = 60  # Total angle range (min to max)

        # Calculate duration from sweeps
        # One sweep = go left-to-right-to-left = 2x angle range
        sweep_time = (self.angle_range * 2) / self.sweep_speed
        self.duration = sweep_time * self.num_sweeps

        self.movement_type = (
            "idle"  # idle, chase, strafe_left, strafe_right, charge, retreat
        )
        self.movement_speed = 0

        self.fire_rate = 0.25
        self.bullet_speed = 300

    def _on_start(self):
        # Override part spray speed
        for part in self.parts.values():
            if not getattr(part, "is_static", False):
                part.spray_speed = self.sweep_speed

    def _on_update(self, dt):
        played_sound_current_frame = False
        for part in self.parts.values():
            if not part.active or getattr(part, "is_static", False):
                continue
            part.spray_rotate(dt)
            if "mg" in part.name:
                if self._shoot_bouncing(part, dt):
                    if not played_sound_current_frame:
                        get_sound_manager().play_bfx("boss_bounce_shot")
                        played_sound_current_frame = True

    def _shoot_bouncing(self, part, dt):
        """Fire bouncing bullets from part."""

        if not part.active or not self.bullet_manager:
            return False

        part.fire_timer += dt
        if part.fire_timer < part.fire_rate:
            return False

        part.fire_timer = 0.0

        # Calculate firing direction
        fire_angle_deg = part.base_angle + part.angle
        fire_angle_rad = math.radians(fire_angle_deg)

        dir_x = math.sin(fire_angle_rad)
        dir_y = -math.cos(fire_angle_rad)

        # Spawn position
        muzzle_offset = part.image.get_height() / 2
        spawn_x = part.pos.x + dir_x * muzzle_offset
        spawn_y = part.pos.y + dir_y * muzzle_offset

        # Velocity
        vel_x = dir_x * part.bullet_speed
        vel_y = dir_y * part.bullet_speed

        # Spawn bouncing bullet
        self.bullet_manager.spawn_custom(
            BouncingBullet,
            pos=(spawn_x, spawn_y),
            vel=(vel_x, vel_y),
            image=part.spray_bullet_image,  # Use trace bullet sprite
            owner="enemy",
            damage=1,
            max_bounces=3,
        )
        return True


@attack(enabled=True)
class ChargeAttack(BossAttack):
    """Multi-phase charge attack with off-screen dives."""

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)

        # === TIMING CONFIG ===
        self.duration = float("inf")
        self.warn_time = 1.0
        self.rotate_time = 0.3
        self.track_time = 0.8
        self.cooldown_time = 1.0

        # === MOVEMENT CONFIG ===
        self.charge_speed = 2000
        self.return_speed = 100
        self.total_charges = 4

        # === MINE CONFIG ===
        self.mines_enabled = False
        self.mine_interval = 0.1

        # === RUNTIME STATE (reset in _on_start) ===
        self.phase = "warn"
        self.phase_timer = 0.0
        self.charge_count = 0
        self.going_down = True
        self.mine_timer = 0.0

        # === COMPUTED (set in _on_start) ===
        self.bottom_y = 0
        self.top_y = 0

        # === VISUALS ===
        self._init_warning_emitter()
        self._init_phase_handlers()

    def _on_update(self, dt):
        self.phase_timer += dt
        self.warning_emitter.update(dt)

        # Dispatch to phase handler
        handler = self._phase_handlers.get(self.phase)
        if handler:
            handler(dt)

    def _init_phase_handlers(self):
        """Map phase names to handler methods."""
        self._phase_handlers = {
            "warn": self._phase_warn,
            "charge": self._phase_charge,
            "rotate": self._phase_rotate,
            "track": self._phase_track,
            "cooldown": self._phase_cooldown,
            "return": self._phase_return,
        }

    # --- Individual Phase Methods ---

    def _phase_warn(self, dt):
        """On-screen pause with debris warning."""
        self._emit_warning_debris(dt)
        if self.phase_timer >= self.warn_time:
            self._next_phase("charge")

    def _phase_charge(self, dt):
        """Vertical charge through screen, optional mines."""
        self._emit_warning_debris(dt)
        self._try_spawn_mine(dt)

        # Move vertically
        direction = 1 if self.going_down else -1
        self.boss.pos.y += direction * self.charge_speed * dt
        self.boss.anchor_pos.xy = self.boss.pos.xy

        # Check if reached edge
        target_y = self.bottom_y if self.going_down else self.top_y
        past_target = (
            (self.boss.pos.y >= target_y)
            if self.going_down
            else (self.boss.pos.y <= target_y)
        )

        if past_target:
            self.boss.pos.y = target_y
            self._next_phase("rotate")

    def _phase_rotate(self, dt):
        """Off-screen rotation/flip."""
        if self.phase_timer >= self.rotate_time:
            next_phase = (
                "cooldown" if self.charge_count >= self.total_charges else "track"
            )
            self._next_phase(next_phase)

    def _phase_track(self, dt):
        """Off-screen, follow player X position."""
        if self.player_ref:
            self.boss.pos.x = self.player_ref.pos.x
        if self.phase_timer >= self.track_time:
            self._next_phase("warn")

    def _phase_cooldown(self, dt):
        """Brief pause after all charges complete."""
        if self.phase_timer >= self.cooldown_time:
            self._next_phase("return")

    def _phase_return(self, dt):
        """Slow return to home position."""
        self.boss.body_rotation = 0
        direction = self.boss.home_pos - self.boss.pos
        dist = direction.length()

        if dist < 10:
            self.boss.pos.xy = self.boss.home_pos.xy
            self.boss.anchor_pos.xy = self.boss.home_pos.xy
            self.finish()
        else:
            direction.normalize_ip()
            self.boss.pos += direction * self.return_speed * dt
            self.boss.anchor_pos.xy = self.boss.home_pos.xy

    # === SETUP METHODS ===

    def _init_warning_emitter(self):
        """Initialize debris particle emitter."""
        dirt_colors = [
            (139, 90, 43),
            (160, 120, 80),
            (100, 80, 60),
            (120, 100, 70),
            (90, 60, 30),
        ]
        self.warning_emitter = DebrisEmitter(
            emit_rate=200, max_particles=600, colors=dirt_colors
        )

    def _on_start(self):
        """Reset state for new attack cycle."""
        self.phase = "warn"
        self.phase_timer = 0.0
        self.charge_count = 0
        self.going_down = True
        self.mine_timer = 0.0
        self.boss.entrance_complete = True

        # Compute screen bounds
        half_height = self.boss.rect.height // 2
        self.bottom_y = Display.HEIGHT + half_height + 200
        self.top_y = -half_height - 200

        get_sound_manager().play_bfx("boss_charge_load")

        get_events().dispatch(ScreenShakeEvent(intensity=1.5, duration=self.warn_time))

    # === PHASE TRANSITION ===

    def _next_phase(self, phase):
        """Transition to new phase with entry effects."""
        self.phase = phase
        self.phase_timer = 0.0

        if phase == "warn":
            get_sound_manager().play_bfx("boss_charge_load")
            get_events().dispatch(
                ScreenShakeEvent(intensity=3.0, duration=self.warn_time + 0.5)
            )
        elif phase == "charge":
            get_sound_manager().play_bfx("boss_charge")
            get_events().dispatch(ScreenShakeEvent(intensity=8.0, duration=2.0))
        elif phase == "rotate":
            self.going_down = not self.going_down
            self.boss.body_rotation = 0 if self.going_down else 180
            self.boss.sync_parts_to_body()
            self.charge_count += 1
        elif phase == "return":
            self.boss.pos.x = Display.WIDTH // 2

    # === HELPERS ===

    def _try_spawn_mine(self, dt):
        """Spawn mine at interval during charge."""
        if not self.mines_enabled:
            return
        self.mine_timer += dt
        if self.mine_timer >= self.mine_interval:
            self.mine_timer = 0.0
            self._spawn_mine()

    def _spawn_mine(self):
        """Drop a mine at boss position."""
        if not self.boss.hazard_manager:
            return
        if 0 < self.boss.pos.y < Display.HEIGHT:
            self.boss.hazard_manager.spawn(TimedMine, self.boss.pos.x, self.boss.pos.y)

    def _emit_warning_debris(self, dt):
        """Emit debris in warning zone at boss X position."""
        width = self.boss.rect.width + 40
        x = int(self.boss.pos.x - width // 2)
        warn_rect = pygame.Rect(x, 0, width, Display.HEIGHT)
        self.warning_emitter.emit_continuous(warn_rect, dt)

    # === CLEANUP & OVERRIDES ===

    def _on_finish(self):
        self.phase = "idle"
        self.boss.body_rotation = 0

    def get_movement_override(self):
        return (0, 0)

    def draw_warning(self, draw_manager):
        """Draw debris warning effect."""
        self.warning_emitter.render(draw_manager, layer=Layers.BACKGROUND + 1)


@attack(enabled=False)
class MineCharge(BossAttack):
    """Horizontal charge attack. TODO: Add mine trail."""

    def __init__(self, boss, bullet_manager):
        super().__init__(boss, bullet_manager)

        # Timing config
        self.warn_time = 0.8  # Initial warning on screen
        self.retreat_speed = 150  # Slow retreat upward
        self.track_time = 0.6  # Off-screen player Y tracking
        self.charge_warn_time = 0.8  # Warning before charge
        self.charge_speed = 1800  # Fast horizontal charge
        self.return_speed = 120  # Slow return to home

        self.duration = 15.0  # Failsafe max duration

        self.screen_width = Display.WIDTH
        self.screen_height = Display.HEIGHT

        # State
        self.phase = "warn"
        self.phase_timer = 0.0
        self.charge_direction = 1  # 1 = left→right, -1 = right→left
        self.charge_y = 0

        # Boundary positions (set in _on_start)
        self.top_y = 0
        self.left_x = 0
        self.right_x = 0

        # Warning emitter (horizontal band)
        dirt_colors = [
            (139, 90, 43),
            (160, 120, 80),
            (100, 80, 60),
            (120, 100, 70),
            (90, 60, 30),
        ]
        self.warning_emitter = DebrisEmitter(
            emit_rate=200, max_particles=600, colors=dirt_colors
        )

    def _on_start(self):
        self.phase = "warn"
        self.phase_timer = 0.0
        self.charge_direction = random.choice([-1, 1])
        self.boss.entrance_complete = True

        get_sound_manager().play_bfx("boss_charge_load")

        # Disable arm hitboxes during charge
        for part in self.parts.values():
            if not getattr(part, "is_static", False) and part.hitbox:
                part.hitbox.set_active(False)

        self._original_body_image = self.boss.body_image
        self._original_part_images = {
            name: part._base_image for name, part in self.parts.items()
        }
        self._original_part_offsets = {
            name: pygame.Vector2(part.offset.x, part.offset.y)
            for name, part in self.parts.items()
        }
        self.charge_scale = 0.8

        # Calculate offset from boss body image + buffer
        if self.boss.body_image:
            boss_height = self.boss.body_image.get_height()
            boss_width = self.boss.body_image.get_width()
        else:
            boss_height = 300
            boss_width = 300

        buffer = 200  # Extra clearance
        self.top_y = -(boss_height // 2) - buffer
        self.left_x = -(boss_width // 2) - buffer
        self.right_x = self.screen_width + (boss_width // 2) + buffer

        get_events().dispatch(ScreenShakeEvent(intensity=1.5, duration=self.warn_time))

    def _on_update(self, dt):
        self.phase_timer += dt
        self.warning_emitter.update(dt)

        if self.phase == "warn":
            # Initial warning while visible
            if self.phase_timer >= self.warn_time:
                self._next_phase("retreat")

        elif self.phase == "retreat":
            # Slow move up off screen
            self.boss.pos.y -= self.retreat_speed * dt
            # Sync anchor to prevent spring-back
            self.boss.anchor_pos.xy = self.boss.pos.xy
            if self.boss.pos.y < self.top_y:
                self._next_phase("reposition")

        elif self.phase == "reposition":
            # Shrink boss for charge
            self._apply_scale(self.charge_scale)

            # Instant teleport to side
            if self.charge_direction == 1:
                self.boss.pos.x = self.left_x
                self.boss.body_rotation = -90  # Face right
            else:
                self.boss.pos.x = self.right_x
                self.boss.body_rotation = 90  # Face left

            self.boss.sync_parts_to_body()

            # Set Y to exact screen center
            self.charge_y = self.screen_height / 2
            self.boss.pos.y = self.charge_y
            self.boss.anchor_pos.xy = self.boss.pos.xy
            self._next_phase("charge_warn")

        elif self.phase == "charge_warn":
            get_sound_manager().play_bfx("boss_charge_load")
            # Emit horizontal warning band
            self._emit_warning_debris(dt)
            self.boss.sync_parts_to_body()
            if self.phase_timer >= self.charge_warn_time:
                self._next_phase("charge")

        elif self.phase == "charge":
            get_sound_manager().play_bfx("boss_charge")
            # Fast horizontal charge
            self._emit_warning_debris(dt)
            self.boss.pos.x += self.charge_direction * self.charge_speed * dt
            self.boss.anchor_pos.xy = self.boss.pos.xy

            self.boss.sync_parts_to_body()

            if self.charge_direction == 1 and self.boss.pos.x > self.right_x:
                self._next_phase("reposition_top")
            elif self.charge_direction == -1 and self.boss.pos.x < self.left_x:
                self._next_phase("reposition_top")

        elif self.phase == "reposition_top":
            # Restore original size
            self._restore_scale()

            self.boss.pos.x = self.screen_width // 2
            self.boss.pos.y = self.top_y
            self.boss.body_rotation = 0  # Face down (normal)
            self.boss.sync_parts_to_body()
            self._next_phase("return")

        elif self.phase == "return":
            # Slow descent to home
            direction = self.boss.home_pos - self.boss.pos
            dist = direction.length()
            if dist < 10:
                self.boss.pos.xy = self.boss.home_pos.xy
                self.boss.anchor_pos.xy = self.boss.home_pos.xy
                self.finish()
            else:
                direction.normalize_ip()
                self.boss.pos += direction * self.return_speed * dt
                self.boss.anchor_pos.xy = self.boss.pos.xy

    def _next_phase(self, phase):
        self.phase = phase
        self.phase_timer = 0.0

        if phase == "charge_warn":
            get_events().dispatch(
                ScreenShakeEvent(intensity=2.0, duration=self.charge_warn_time)
            )
        elif phase == "charge":
            get_events().dispatch(ScreenShakeEvent(intensity=6.0, duration=1.5))

    def _emit_warning_debris(self, dt):
        """Emit debris in horizontal warning band."""
        height = self.boss.rect.height + 40
        y = int(self.charge_y - height // 2)
        warn_rect = pygame.Rect(0, y, self.screen_width, height)
        self.warning_emitter.emit_continuous(warn_rect, dt)

    def _on_finish(self):
        """Ensure scale is restored if attack ends early."""
        self._restore_scale()
        self.boss.body_rotation = 0
        self.boss.sync_parts_to_body()

        # Re-enable arm hitboxes
        for part in self.parts.values():
            if not getattr(part, "is_static", False) and part.hitbox:
                part.hitbox.set_active(True)

    def get_movement_override(self):
        return (0, 0)

    def draw_warning(self, draw_manager):
        """Draw debris warning effect."""
        self.warning_emitter.render(draw_manager, layer=Layers.BACKGROUND + 1)

    def _apply_scale(self, scale):
        """Shrink boss and parts."""
        # Scale body
        orig = self._original_body_image
        new_size = (int(orig.get_width() * scale), int(orig.get_height() * scale))
        self.boss.body_image = pygame.transform.scale(orig, new_size)
        self.boss.rect = self.boss.body_image.get_rect(
            center=(int(self.boss.pos.x), int(self.boss.pos.y))
        )

        # Scale parts
        for name, part in self.parts.items():
            orig_part = self._original_part_images.get(name)
            if orig_part:
                new_size = (
                    int(orig_part.get_width() * scale),
                    int(orig_part.get_height() * scale),
                )
                part._base_image = pygame.transform.scale(orig_part, new_size)
                part.image = part._base_image
                part.offset.x *= scale
                part.offset.y *= scale

    def _restore_scale(self):
        """Restore original boss size."""
        self.boss.body_image = self._original_body_image
        self.boss.rect = self.boss.body_image.get_rect(
            center=(int(self.boss.pos.x), int(self.boss.pos.y))
        )

        for name, part in self.parts.items():
            orig_part = self._original_part_images.get(name)
            orig_offset = self._original_part_offsets.get(name)
            if orig_part:
                part._base_image = orig_part
                part.image = orig_part
            if orig_offset:
                part.offset.x = orig_offset.x
                part.offset.y = orig_offset.y
