"""
anim_motion.py
---------------
Provides visual motion-style effects such as shake, tilt, and spin,
used to enhance feedback and cinematic impact.

Responsibilities
----------------
- Modify rendered sprite appearance only (rotation or offset).
- Never modify actual position, hitbox, or physics attributes.
- Provide reusable motion primitives for use in entity animations.
"""

import pygame
import math, random
from src.core.debug.debug_logger import DebugLogger


# ===========================================================
#  POSITIONAL SHAKE (Impact Feedback)
# ===========================================================
def shake_position(entity, t: float, intensity: float = 5.0):
    """
    Visually jitter the sprite position around its true center.
    Does not modify logical position — purely render illusion.

    Args:
        entity: Target entity to shake.
        t (float): Normalized time (0.0 → 1.0).
        intensity (float): Maximum shake radius in pixels.
    """
    try:
        if not hasattr(entity, "rect"):
            return
        # Randomized offset that decays over time
        offset_x = random.uniform(-intensity, intensity) * (1 - t)
        offset_y = random.uniform(-intensity, intensity) * (1 - t)
        entity.rect.center = (entity.pos.x + offset_x, entity.pos.y + offset_y)
    except Exception as e:
        DebugLogger.warn(f"[anim_motion.shake_position] Failed: {e}")


# ===========================================================
#  ANGULAR TILT (Smooth Banking)
# ===========================================================
def tilt(entity, t: float, max_angle: float = 15.0):
    """
    Smoothly rotates the sprite left/right visually, simulating a bank or dodge.
    Does not affect collision or movement.

    Args:
        entity: Target entity.
        t (float): Normalized time (0.0 → 1.0).
        max_angle (float): Maximum tilt in degrees.
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        angle = max_angle * math.sin(math.pi * t)
        rotated = pygame.transform.rotate(entity.image, angle)
        entity.image = rotated
    except Exception as e:
        DebugLogger.warn(f"[anim_motion.tilt] Failed: {e}")


# ===========================================================
#  FULL SPIN (Continuous Rotation)
# ===========================================================
def spin_visual(entity, t: float, total_angle: float = 360.0):
    """
    Rotates the sprite around its center for the full duration.

    Args:
        entity: Target entity.
        t (float): Normalized time (0.0 → 1.0).
        total_angle (float): Degrees of total rotation.
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        angle = total_angle * t
        rotated = pygame.transform.rotate(entity.image, angle)
        entity.image = rotated
    except Exception as e:
        DebugLogger.warn(f"[anim_motion.spin_visual] Failed: {e}")


# ===========================================================
#  ROTATIONAL WOBBLE (Subtle Oscillation)
# ===========================================================
def wobble_rotation(entity, t: float, angle: float = 10.0, frequency: float = 5.0):
    """
    Oscillates sprite rotation for subtle wobble or hover effects.

    Args:
        entity: Target entity.
        t (float): Normalized animation time (0.0 → 1.0).
        angle (float): Max oscillation angle in degrees.
        frequency (float): Oscillation frequency in Hz.
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        theta = angle * math.sin(2 * math.pi * frequency * t)
        rotated = pygame.transform.rotate(entity.image, theta)
        entity.image = rotated
    except Exception as e:
        DebugLogger.warn(f"[anim_motion.wobble_rotation] Failed: {e}")


# ===========================================================
#  ROTATIONAL SHAKE (Angular Jitter)
# ===========================================================
def shake_rotation(entity, t: float, intensity: float = 5.0):
    """
    Adds small random angular jitter to simulate impact vibration.

    Args:
        entity: Target entity.
        t (float): Normalized time (0.0 → 1.0).
        intensity (float): Max rotation deviation in degrees.
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        angle = random.uniform(-intensity, intensity) * (1 - t)
        rotated = pygame.transform.rotate(entity.image, angle)
        entity.image = rotated
    except Exception as e:
        DebugLogger.warn(f"[anim_motion.shake_rotation] Failed: {e}")


# ===========================================================
#  VIBRATION (Tiny High-Frequency Offset)
# ===========================================================
def vibrate_visual(entity, t: float, amplitude: float = 3.0, frequency: float = 20.0):
    """
    Creates high-frequency micro jitter to simulate electrical instability.
    Used for energy effects or charged states.

    Args:
        entity: Target entity.
        t (float): Normalized time (0.0 → 1.0).
        amplitude (float): Maximum pixel displacement.
        frequency (float): Number of oscillations per second.
    """
    try:
        if not hasattr(entity, "rect"):
            return

        offset_x = amplitude * math.sin(2 * math.pi * frequency * t)
        offset_y = amplitude * math.cos(2 * math.pi * frequency * t)
        entity.rect.center = (entity.pos.x + offset_x, entity.pos.y + offset_y)
    except Exception as e:
        DebugLogger.warn(f"[anim_motion.vibrate_visual] Failed: {e}")
