"""
player.py
---------
Player-specific animation definitions (Tier 2).

All player animations centralized here for easy tuning.
"""

from src.graphics.animations.animation_effects.death_animation import death_fade
from src.graphics.animations.animation_effects.common_animation import blink, fade_color
from src.core.debug.debug_logger import DebugLogger
from src.graphics.animations.animation_registry import register


# ============================================================
# Death Animations
# ============================================================
@register("player", "death")
def death_player(entity, t):
    """
    Standard player death: fade out over 1 second.

    Args:
        entity: Player instance
        t: Normalized time (0.0 to 1.0)
    """
    return death_fade(entity, t)


# ============================================================
# Damage Animations
# ============================================================
@register("player", "damage")
def damage_player(entity, t):
    ctx = getattr(entity, 'anim_context', {})
    interval = ctx.get('blink_interval', 0.1)
    previous_state = ctx.get('previous_state', entity._current_sprite)
    target_state = ctx.get('target_state', entity._current_sprite)

    if entity.render_mode == "shape":
        start_color = entity.get_target_color(previous_state)
        end_color = entity.get_target_color(target_state)

        # Lerp color directly
        current_color = tuple(
            int(start_color[i] + (end_color[i] - start_color[i]) * t)
            for i in range(3)
        )

        # Rebake shape with interpolated color
        entity.refresh_sprite(new_color=current_color)

        # Apply blink on top
        blink(entity, t, interval=interval)
    else:
        # Image mode - just blink (no color fade)
        blink(entity, t, interval=interval)

    # Cleanup at end
    if t >= 1.0 and hasattr(entity, '_original_image'):
        entity.image = entity._original_image.copy()
        entity.image.set_alpha(255)