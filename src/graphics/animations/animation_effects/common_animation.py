"""Common reusable animation effects."""
import pygame


def fade_out(entity, t):
    """Fade entity from opaque to transparent."""
    alpha = int(255 * (1.0 - t))
    # Copy image to avoid mutating shared cached surface
    if entity.image.get_alpha() != alpha:
        entity.image = entity.image.copy()
        entity.image.set_alpha(alpha)


def fade_in(entity, t):
    """Fade entity from transparent to opaque."""
    alpha = int(255 * t)
    if entity.image.get_alpha() != alpha:
        entity.image = entity.image.copy()  # Add this line
        entity.image.set_alpha(alpha)


def scale_down(entity, t):
    """Shrink entity to 0."""
    scale = 1.0 - t
    if scale <= 0:
        return

    orig = getattr(entity, '_original_image', entity.image)
    new_size = (
        max(1, int(orig.get_width() * scale)),
        max(1, int(orig.get_height() * scale))
    )
    entity.image = pygame.transform.scale(orig, new_size)
    entity.rect = entity.image.get_rect(center=entity.rect.center)


def blink(entity, t, interval=0.1):
    """
    Blink based on a fixed time interval (seconds), NOT based on animation length.
    `t` is normalized 0..1 so AnimationPlayer must pass real time.
    """
    # Convert normalized t back to elapsed time (AnimationPlayer provides this)
    elapsed = entity.anim_context.get("elapsed_time", None)

    if elapsed is None:
        # Fallback: behave like old blink
        alpha = 255 if int(t * (1.0 / interval)) % 2 == 0 else 0
        entity.image.set_alpha(alpha)
        return

    # True time-based blink
    if int(elapsed / interval) % 2 == 0:
        entity.image.set_alpha(255)
    else:
        entity.image.set_alpha(0)


def fade_color(entity, t, start_color=(255, 0, 0), end_color=(0, 0, 0)):
    """
    Apply additive color flash overlay (e.g., red damage flash).
    NOT for blending between base colors - use direct rebaking for that.

    Use case: Flash red on hit, fade to normal
    """
    orig = getattr(entity, '_original_image', entity.image)

    # Lerp flash intensity
    r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
    g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
    b = int(start_color[2] + (end_color[2] - start_color[2]) * t)

    flash = orig.copy()
    flash.fill((r, g, b), special_flags=pygame.BLEND_RGB_ADD)

    # Preserve alpha (important for blink)
    current_alpha = entity.image.get_alpha()
    entity.image = flash
    entity.image.set_alpha(current_alpha)


def sprite_cycle(entity, t, frame_key='death_frames'):
    """
    Generic frame cycling - works for any animation type.

    Args:
        entity: Entity with anim_context containing frames
        t: Normalized time 0..1
        frame_key: Key in anim_context dict (e.g., 'death_frames', 'attack_frames')
    """
    ctx = getattr(entity, 'anim_context', {})
    frames = ctx.get(frame_key, [])

    if not frames:
        # Fallback to fade if no frames provided
        fade_out(entity, t)
        return

    # Calculate frame index with even distribution
    frame_idx = min(int(t * len(frames)), len(frames) - 1)
    entity.image = frames[frame_idx]
