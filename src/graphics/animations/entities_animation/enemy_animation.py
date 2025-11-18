"""
enemy_animation.py
------------------
Enemy-specific animation definitions.

All enemy animations centralized here for easy tuning.
Enemies share common damage/death patterns but can be customized per type.
"""

from src.graphics.animations.animation_effects.common_animation import blink, fade_out
from src.graphics.animations.animation_registry import register
from src.core.debug.debug_logger import DebugLogger
from src.graphics.animations.animation_effects.death_animation import death_fade, death_sprite_cycle  # Add death_sprite_cycle


# ============================================================
# Death Animations
# ============================================================

@register("enemy", "death")
def death_enemy(entity, t):
    """
    Standard enemy death: fade out over time.

    Shared across all enemy types for consistency.

    Args:
        entity: Enemy instance
        t: Normalized time (0.0 to 1.0)
    """
    ctx = getattr(entity, 'anim_context', {})

    if ctx.get('death_frames'):
        death_sprite_cycle(entity, t)
    else:
        death_fade(entity, t)


# ============================================================
# Damage Animations
# ============================================================

@register("enemy", "damage")
def damage_enemy(entity, t):
    """
    Standard enemy damage: blink effect.

    Uses context for customizable blink interval.

    Args:
        entity: Enemy instance
        t: Normalized time (0.0 to 1.0)
    """
    ctx = getattr(entity, 'anim_context', {})
    interval = ctx.get('blink_interval', 0.08)  # Faster blink than player

    blink(entity, t, interval=interval)

    # Cleanup at end
    if t >= 1.0:
        if hasattr(entity, 'image'):
            entity.image.set_alpha(255)

# ============================================================
# Specialized Enemy Animations (Future)
# ============================================================

# Example: Boss-specific death with explosion sequence
# @register("enemy_boss", "death")
# def death_boss(entity, t):
#     # Multi-phase death animation
#     pass

# Example: Shooter muzzle flash
# @register("enemy_shooter", "shoot")
# def shoot_flash(entity, t):
#     # Brief flash when firing
#     pass