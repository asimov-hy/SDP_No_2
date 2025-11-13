"""Common reusable animation effects."""
import pygame

def fade_out(entity, t):
    """Fade entity from opaque to transparent."""
    alpha = int(255 * (1.0 - t))
    entity.image.set_alpha(alpha)


def fade_in(entity, t):
    """Fade entity from transparent to opaque."""
    alpha = int(255 * t)
    entity.image.set_alpha(alpha)


def scale_down(entity, t):
    """Shrink entity to 0."""
    if not hasattr(entity, '_original_image'):
        entity._original_image = entity.image.copy()

    scale = 1.0 - t
    if scale <= 0:
        return

    new_size = (
        max(1, int(entity._original_image.get_width() * scale)),
        max(1, int(entity._original_image.get_height() * scale))
    )
    entity.image = pygame.transform.scale(entity._original_image, new_size)
    entity.rect = entity.image.get_rect(center=entity.rect.center)


def blink(entity, t, frequency=8):
    """Flash entity on/off."""
    alpha = 255 if int(t * frequency) % 2 == 0 else 0
    entity.image.set_alpha(alpha)