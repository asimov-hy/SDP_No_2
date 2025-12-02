"""
player.py
---------
Player-specific animation definitions (Tier 2).

All player animations centralized here for easy tuning.
"""

import pygame
import math

from src.graphics.animations.animation_effects.common_animation import (
    flash_white,
    shake,
)

from src.graphics.particles.particle_manager import ParticleEmitter

from src.graphics.animations.animation_registry import register


# ============================================================
# Death Animations
# ============================================================
@register("player", "death")
def death_player(entity, t):
    """
    Player death: long shake with particles -> explosion + disappear.
    """
    ctx = getattr(entity, "anim_context", {})

    # Phase 1: Shake with particles (0.0 - 0.8)
    if t < 0.8:
        shake(entity, t / 0.8, intensity=8, frequency=50)

        if not hasattr(entity, "_death_emit_timer"):
            entity._death_emit_timer = 0
        entity._death_emit_timer += 1
        if entity._death_emit_timer % 3 == 0:
            ParticleEmitter.burst("player_death_buildup", entity.rect.center, count=4)

    # Phase 2: Explosion + disappear (at 0.8)
    if t >= 0.8 and not ctx.get("_exploded", False):
        ctx["_exploded"] = True
        ParticleEmitter.burst("player_death_explode", entity.rect.center, count=35)
        entity.image.set_alpha(0)  # Instant disappear
        if hasattr(entity, "_death_emit_timer"):
            del entity._death_emit_timer


# ============================================================
# Damage Animations
# ============================================================
@register("player", "damage")
def damage_player(entity, t):
    ctx = getattr(entity, "anim_context", {})
    interval = ctx.get("blink_interval", 0.1)
    previous_state = ctx.get("previous_state", entity._current_sprite)
    target_state = ctx.get("target_state", entity._current_sprite)

    if entity.render_mode == "shape":
        start_color = entity.get_target_color(previous_state)
        end_color = entity.get_target_color(target_state)

        # Lerp color directly
        current_color = tuple(
            int(start_color[i] + (end_color[i] - start_color[i]) * t) for i in range(3)
        )

        # Rebake shape with interpolated color
        entity.refresh_sprite(new_color=current_color)

        # Apply blink on top
        flash_white(entity, t, interval=interval)
    else:
        # Image mode - just blink (no color fade)
        flash_white(entity, t, interval=interval)

    # Cleanup at end
    if t >= 1.0 and hasattr(entity, "_original_image"):
        entity.image = entity._original_image.copy()
        entity.image.set_alpha(255)


# ============================================================
# State Animation
# ============================================================
@register("player", "stun")
def stun_player(entity, t):
    """
    STUN state: Strong white flash + fast blink.
    Called during knockback phase.
    """
    # Cache base image
    if not hasattr(entity, "_base_image") or entity._base_image is None:
        entity._base_image = entity.image.copy()

    # Red tint
    base = entity._base_image
    flash = base.copy()
    flash.fill((255, 50, 50), special_flags=pygame.BLEND_RGB_ADD)

    # Fast blink
    elapsed = entity.anim_context.get("elapsed_time", 0)
    if int(elapsed / 0.05) % 2 == 0:
        flash.set_alpha(255)
    else:
        flash.set_alpha(80)

    entity.image = flash


@register("player", "recovery")
def recovery_player(entity, t):
    """
    RECOVERY state: Orange/yellow pulse on player.
    Shield visuals handled by Shield entity.
    """
    # Cache base image
    if not hasattr(entity, "_base_image") or entity._base_image is None:
        entity._base_image = entity.image.copy()

    base = entity._base_image
    elapsed = entity.anim_context.get("elapsed_time", 0)

    # Player tint: pulsing orange/yellow
    tinted = base.copy()
    pulse = 0.5 + 0.5 * math.sin(elapsed * 4)
    orange = int(60 + 30 * pulse)
    yellow = int(30 + 20 * pulse)
    tinted.fill((orange, yellow, 0), special_flags=pygame.BLEND_RGB_ADD)
    entity.image = tinted

    # Cleanup at end
    if t >= 1.0:
        entity.image = entity._base_image.copy()
        entity.image.set_alpha(255)
        if hasattr(entity, "_base_image"):
            del entity._base_image
