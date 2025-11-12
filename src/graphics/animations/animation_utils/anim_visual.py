"""
anim_visual.py
---------------
Defines lightweight visual-only animation utilities that modify
an entity's appearance (sprite, alpha, or color), without affecting
its position, hitbox, or gameplay logic.

Responsibilities
----------------
- Provide basic visual transformations such as fading and tinting.
- Support composable per-entity effects used by animation scripts.
- Never modify entity physics, position, or game state.
"""

import pygame
from src.core.debug.debug_logger import DebugLogger


# ===========================================================
#  FADE EFFECTS
# ===========================================================
def fade_in(entity, t: float):
    """
    Gradually increase sprite alpha (transparency) from 0 → 255.

    Args:
        entity: Target entity whose image will be modified.
        t (float): Normalized progress (0.0 → 1.0).
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        alpha = min(255, int(255 * t))
        entity.image.set_alpha(alpha)
    except Exception as e:
        DebugLogger.warn(f"[anim_visual.fade_in] Failed: {e}")


def fade_out(entity, t: float):
    """
    Gradually decrease sprite alpha (transparency) from 255 → 0.

    Args:
        entity: Target entity whose image will be modified.
        t (float): Normalized progress (0.0 → 1.0).
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        alpha = max(0, int(255 * (1 - t)))
        entity.image.set_alpha(alpha)
    except Exception as e:
        DebugLogger.warn(f"[anim_visual.fade_out] Failed: {e}")


# ===========================================================
#  COLOR EFFECTS
# ===========================================================
def color_tint(entity, color: tuple[int, int, int], t: float):
    """
    Gradually blend the entity's image toward a target color.
    Only modifies pixel appearance; does not affect collisions.

    Args:
        entity: Target entity whose image will be tinted.
        color (tuple[int, int, int]): RGB color target.
        t (float): Normalized interpolation factor (0.0 → 1.0).
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        # Create a surface filled with the tint color
        overlay = pygame.Surface(entity.image.get_size(), pygame.SRCALPHA)
        r, g, b = [int(c * t) for c in color]
        overlay.fill((r, g, b, 0))

        # Blend the color additively with the sprite
        entity.image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    except Exception as e:
        DebugLogger.warn(f"[anim_visual.color_tint] Failed: {e}")


def flash_color(entity, color: tuple[int, int, int], t: float, interval: float = 0.1):
    """
    Temporarily flash the entity with a given color at a set interval.
    Does not affect gameplay or logical state — purely visual.

    Args:
        entity: Target entity whose image will flash.
        color (tuple[int, int, int]): RGB flash color.
        t (float): Normalized animation time (0.0 → 1.0).
        interval (float): Flash period in seconds.
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        # Alternate flashing based on normalized time and interval
        phase = int((t / interval) % 2)
        if phase == 0:
            overlay = pygame.Surface(entity.image.get_size(), pygame.SRCALPHA)
            overlay.fill(color)
            entity.image.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    except Exception as e:
        DebugLogger.warn(f"[anim_visual.flash_color] Failed: {e}")


# ===========================================================
#  SCALE / SIZE EFFECTS
# ===========================================================
def scale_down(entity, t: float, factor: float = 0.5):
    """
    Gradually scale down the entity's sprite.
    The transformation is visual-only — the hitbox remains unchanged.

    Args:
        entity: Target entity.
        t (float): Normalized time (0.0 → 1.0).
        factor (float): Minimum scale multiplier (default: 0.5).
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        scale = max(factor, 1 - (1 - factor) * t)
        w, h = entity.image.get_size()
        new_img = pygame.transform.smoothscale(entity.image, (int(w * scale), int(h * scale)))
        entity.image = new_img
    except Exception as e:
        DebugLogger.warn(f"[anim_visual.scale_down] Failed: {e}")


def scale_up(entity, t: float, factor: float = 1.5):
    """
    Gradually scale up the entity's sprite (visual expansion).
    The transformation does not affect position or collision radius.

    Args:
        entity: Target entity.
        t (float): Normalized time (0.0 → 1.0).
        factor (float): Maximum scale multiplier (default: 1.5).
    """
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        scale = min(factor, 1 + (factor - 1) * t)
        w, h = entity.image.get_size()
        new_img = pygame.transform.smoothscale(entity.image, (int(w * scale), int(h * scale)))
        entity.image = new_img
    except Exception as e:
        DebugLogger.warn(f"[anim_visual.scale_up] Failed: {e}")


def pulse_scale(entity, t: float, amplitude: float = 0.1, frequency: float = 3.0):
    """
    Repeatedly scales the entity's sprite up and down for a 'breathing' effect.

    Args:
        entity: Target entity.
        t (float): Normalized time (0.0 → 1.0).
        amplitude (float): Scale intensity (default: 0.1 = ±10%).
        frequency (float): Oscillation frequency (cycles per second).
    """
    import math
    if not hasattr(entity, "image") or entity.image is None:
        return

    try:
        scale = 1 + amplitude * math.sin(2 * math.pi * frequency * t)
        w, h = entity.image.get_size()
        new_img = pygame.transform.smoothscale(entity.image, (int(w * scale), int(h * scale)))
        entity.image = new_img
    except Exception as e:
        DebugLogger.warn(f"[anim_visual.pulse_scale] Failed: {e}")
