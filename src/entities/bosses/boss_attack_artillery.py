"""
boss_attack_artillery.py
------------------------
Artillery attack: Rotates to track player, shows aiming laser, fires railgun beam.

Phases:
    1. TRACKING  - Rotate toward player, show thin aiming laser
    2. CHARGING  - Lock angle, laser intensifies
    3. FIRING    - Thick beam damages player
    4. COOLDOWN  - Brief pause before attack ends
"""

import math
import pygame

from src.entities.bosses.boss_attack_base import BossAttack


class ArtilleryAttack(BossAttack):
    """
    Railgun/laser cannon attack with tracking and charge-up.
    """

    # Attack phases
    PHASE_TRACKING = "tracking"
    PHASE_CHARGING = "charging"
    PHASE_FIRING = "firing"
    PHASE_COOLDOWN = "cooldown"

    def __init__(self, part, boss, bullet_manager, draw_manager, config=None):
        super().__init__(part, boss, bullet_manager, draw_manager)

        config = config or {}

        # Timing (seconds)
        self.track_duration = config.get("track_duration", 1.5)
        self.charge_duration = config.get("charge_duration", 0.5)
        self.fire_duration = config.get("fire_duration", 0.3)
        self.cooldown_duration = config.get("cooldown_duration", 0.2)

        # Rotation
        self.rotation_speed = config.get("rotation_speed", 120)  # degrees/sec
        self.current_angle = 270  # Start aiming down

        # Beam properties
        self.beam_range = config.get("beam_range", 800)
        self.beam_damage = config.get("beam_damage", 25)
        self.aim_laser_width = config.get("aim_laser_width", 2)
        self.beam_width = config.get("beam_width", 12)

        # Colors
        self.aim_color = config.get("aim_color", (255, 0, 0, 128))      # Red, transparent
        self.charge_color = config.get("charge_color", (255, 100, 0))   # Orange
        self.beam_color = config.get("beam_color", (255, 255, 100))     # Yellow-white
        self.beam_core_color = config.get("beam_core_color", (255, 255, 255))

        # State
        self.phase = None
        self.phase_timer = 0.0
        self.locked_angle = 0
        self.hit_player_this_frame = False

    def _on_start(self):
        """Begin tracking phase."""
        self.phase = self.PHASE_TRACKING
        self.phase_timer = 0.0
        self.current_angle = self.part.angle  # Start from part's current angle
        self.hit_player_this_frame = False

    def _on_update(self, dt) -> bool:
        """
        Update attack based on current phase.

        Returns:
            True when attack complete
        """
        self.phase_timer += dt

        if self.phase == self.PHASE_TRACKING:
            return self._update_tracking(dt)

        elif self.phase == self.PHASE_CHARGING:
            return self._update_charging(dt)

        elif self.phase == self.PHASE_FIRING:
            return self._update_firing(dt)

        elif self.phase == self.PHASE_COOLDOWN:
            return self._update_cooldown(dt)

        return True

    # ===================================================================
    # Phase Updates
    # ===================================================================

    def _update_tracking(self, dt) -> bool:
        """Rotate toward player, show aiming laser."""
        # Rotate toward player
        target_angle = self.angle_to_player()
        self.current_angle = self._rotate_toward(
            self.current_angle, target_angle,
            self.rotation_speed * dt
        )
        self.part.angle = self.current_angle

        # Draw aiming laser
        self._draw_aim_laser()

        # Transition to charging
        if self.phase_timer >= self.track_duration:
            self._enter_phase(self.PHASE_CHARGING)

        return False

    def _update_charging(self, dt) -> bool:
        """Lock angle, intensify laser."""
        # Lock angle on first frame
        if self.phase_timer <= dt:
            self.locked_angle = self.current_angle

        # Draw charging laser (pulses)
        pulse = abs(math.sin(self.phase_timer * 15))  # Fast pulse
        width = self.aim_laser_width + int(pulse * 4)
        self._draw_aim_laser(color=self.charge_color, width=width)

        # Transition to firing
        if self.phase_timer >= self.charge_duration:
            self._enter_phase(self.PHASE_FIRING)

        return False

    def _update_firing(self, dt) -> bool:
        """Fire the beam, check for player hit."""
        # Draw thick beam
        self._draw_beam()

        # Check player collision
        self._check_beam_collision()

        # Transition to cooldown
        if self.phase_timer >= self.fire_duration:
            self._enter_phase(self.PHASE_COOLDOWN)

        return False

    def _update_cooldown(self, dt) -> bool:
        """Brief pause after firing."""
        if self.phase_timer >= self.cooldown_duration:
            return True  # Attack complete
        return False

    def _enter_phase(self, phase):
        """Transition to new phase."""
        self.phase = phase
        self.phase_timer = 0.0

    # ===================================================================
    # Rendering
    # ===================================================================

    def _draw_aim_laser(self, color=None, width=None):
        """Draw thin aiming laser from part to max range."""
        color = color or self.aim_color
        width = width or self.aim_laser_width

        start, end = self._get_beam_endpoints(self.current_angle)

        self.draw_manager.queue_shape(
            "line",
            pygame.Rect(0, 0, 0, 0),
            color,
            layer=5,
            start_pos=start,  # ← Correct
            end_pos=end,  # ← Correct
            width=width
        )

    def _draw_beam(self):
        """Draw thick firing beam with core."""
        start, end = self._get_beam_endpoints(self.locked_angle)

        # Outer glow
        self.draw_manager.queue_shape(
            "line",
            pygame.Rect(0, 0, 0, 0),
            self.beam_color,
            layer=5,
            start_pos=start,
            end_pos=end,
            width=self.beam_width
        )

        # Inner core
        self.draw_manager.queue_shape(
            "line",
            pygame.Rect(0, 0, 0, 0),
            self.beam_core_color,
            layer=6,
            start_pos=start,
            end_pos=end,
            width=max(2, self.beam_width // 3)
        )

    def _get_beam_endpoints(self, angle_deg) -> tuple:
        """Calculate beam start and end points."""
        start = (int(self.part.pos.x), int(self.part.pos.y))

        angle_rad = math.radians(angle_deg)
        end_x = self.part.pos.x + math.cos(angle_rad) * self.beam_range
        end_y = self.part.pos.y + math.sin(angle_rad) * self.beam_range
        end = (int(end_x), int(end_y))

        return start, end

    # ===================================================================
    # Collision
    # ===================================================================

    def _check_beam_collision(self):
        """Check if beam intersects player."""
        if not self.player_ref or self.hit_player_this_frame:
            return

        start, end = self._get_beam_endpoints(self.locked_angle)
        player_pos = self.player_ref.pos
        player_radius = getattr(self.player_ref, 'collision_radius', 20)

        # Line-circle collision
        if self._line_circle_collision(start, end, player_pos, player_radius):
            self.player_ref.take_damage(self.beam_damage, source="artillery_beam")
            self.hit_player_this_frame = True

    def _line_circle_collision(self, start, end, center, radius) -> bool:
        """Check if line segment intersects circle."""
        # Vector from start to end
        dx = end[0] - start[0]
        dy = end[1] - start[1]

        # Vector from start to circle center
        fx = start[0] - center.x
        fy = start[1] - center.y

        a = dx * dx + dy * dy
        if a == 0:  # Zero-length line
            # Point-circle collision
            dist_sq = (start[0] - center.x) ** 2 + (start[1] - center.y) ** 2
            return dist_sq <= radius * radius
        b = 2 * (fx * dx + fy * dy)
        c = fx * fx + fy * fy - radius * radius

        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            return False

        discriminant = math.sqrt(discriminant)
        t1 = (-b - discriminant) / (2 * a)
        t2 = (-b + discriminant) / (2 * a)

        # Check if intersection is within line segment
        return (0 <= t1 <= 1) or (0 <= t2 <= 1)

    # ===================================================================
    # Utility
    # ===================================================================

    def _rotate_toward(self, current, target, max_delta) -> float:
        """Smoothly rotate toward target angle."""
        # Normalize angles to 0-360
        current = current % 360
        target = target % 360

        # Find shortest rotation direction
        diff = target - current
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        # Clamp rotation speed
        if abs(diff) < max_delta:
            return target

        return current + math.copysign(max_delta, diff)