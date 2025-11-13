"""Damage/hit reaction effects."""
import pygame
from .common_animation import (blink)


def damage_blink(entity, t):
    """Flash red and blink."""
    blink(entity, t, frequency=10)


def damage_flash(entity, t):
    """Red tint that fades."""
    if not hasattr(entity, '_original_image'):
        entity._original_image = entity.image.copy()

    # Red overlay intensity decreases over time
    intensity = int(255 * (1.0 - t))
    flash_surf = entity._original_image.copy()
    flash_surf.fill((intensity, 0, 0), special_flags=pygame.BLEND_RGB_ADD)
    entity.image = flash_surf