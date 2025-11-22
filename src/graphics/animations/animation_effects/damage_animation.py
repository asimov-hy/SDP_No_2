"""Damage/hit reaction effects."""
import pygame
from .common_animation import (blink)


def damage_blink(entity, t):
    blink(entity, t, interval=0.1)


def damage_flash(entity, t):
    """Red tint that fades."""
    orig = getattr(entity, '_original_image', entity.image)

    # Red overlay intensity decreases over time
    intensity = int(255 * (1.0 - t))
    flash_surf = orig.copy()
    flash_surf.fill((intensity, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
    entity.image = flash_surf