"""Damage/hit reaction effects."""

import pygame
from .common_animation import blink


def damage_blink(entity, t):
    blink(entity, t, interval=0.1)


def damage_flash(entity, t, color=(255, 255, 255)):
    """Tint that fades. Color is a 3-tuple (R, G, B)."""

    orig = (
        entity.image.copy()
        if entity.image
        else getattr(entity, "_base_image", entity.image)
    )

    # Overlay intensity fades out over time
    intensity = int(255 * (1.0 - t))

    flash_surf = orig.copy()

    # Apply adjustable color tint using additive blending
    r = int(color[0] * (intensity / 255))
    g = int(color[1] * (intensity / 255))
    b = int(color[2] * (intensity / 255))

    flash_surf.fill((r, g, b), special_flags=pygame.BLEND_RGB_ADD)

    entity.image = flash_surf
