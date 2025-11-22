"""Death animation variants."""
import pygame
from .common_animation import fade_out, scale_down
from .common_animation import sprite_cycle


def death_fade(entity, t):
    """Simple fade out."""
    fade_out(entity, t)


def death_shrink(entity, t):
    """Fade + shrink."""
    fade_out(entity, t)
    scale_down(entity, t)


def death_spin_fade(entity, t):
    """Rotate while fading."""
    fade_out(entity, t)

    orig = getattr(entity, '_original_image', entity.image)
    angle = t * 360
    entity.image = pygame.transform.rotate(orig, angle)
    entity.rect = entity.image.get_rect(center=entity.rect.center)


def death_sprite_cycle(entity, t):
    """Cycle through death sprite frames."""
    sprite_cycle(entity, t, frame_key='death_frames')
