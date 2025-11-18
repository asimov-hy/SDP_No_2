"""Death animation variants."""
import pygame
from .common_animation import fade_out, scale_down


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

    if not hasattr(entity, '_original_image'):
        entity._original_image = entity.image.copy()

    angle = t * 360
    entity.image = pygame.transform.rotate(entity._original_image, angle)
    entity.rect = entity.image.get_rect(center=entity.rect.center)


# death_animation.py - Add new function
def death_sprite_cycle(entity, t):
    """Cycle through death sprite frames with even timing."""
    ctx = getattr(entity, 'anim_context', {})
    frames = ctx.get('death_frames', [])

    if not frames:
        # Fallback to fade if no frames
        fade_out(entity, t)
        return

    # Even frame distribution
    frame_idx = min(int(t * len(frames)), len(frames) - 1)
    entity.image = frames[frame_idx]