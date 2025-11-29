"""
player.py
---------
Player-specific animation definitions (Tier 2).

All player animations centralized here for easy tuning.
"""

import pygame
import math
from src.graphics.animations.animation_effects.death_animation import death_fade
from src.graphics.animations.animation_effects.common_animation import blink, fade_color, flash_white, shake
from src.graphics.particles.particle_manager import ParticleEmitter
from src.core.debug.debug_logger import DebugLogger
from src.graphics.animations.animation_registry import register


# ============================================================
# Death Animations
# ============================================================
@register("player", "death")
def death_player(entity, t):
    """
    Player death: long shake with particles -> explosion + disappear.
    """
    ctx = getattr(entity, 'anim_context', {})

    # Phase 1: Shake with particles (0.0 - 0.8)
    if t < 0.8:
        shake(entity, t / 0.8, intensity=8, frequency=50)

        if not hasattr(entity, '_death_emit_timer'):
            entity._death_emit_timer = 0
        entity._death_emit_timer += 1
        if entity._death_emit_timer % 3 == 0:
            ParticleEmitter.burst("player_death_buildup", entity.rect.center, count=4)

    # Phase 2: Explosion + disappear (at 0.8)
    if t >= 0.8 and not ctx.get('_exploded', False):
        ctx['_exploded'] = True
        ParticleEmitter.burst("player_death_explode", entity.rect.center, count=35)
        entity.image.set_alpha(0)  # Instant disappear
        if hasattr(entity, '_death_emit_timer'):
            del entity._death_emit_timer


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
        flash_white(entity, t, interval=interval)
    else:
        # Image mode - just blink (no color fade)
        flash_white(entity, t, interval=interval)

    # Cleanup at end
    if t >= 1.0 and hasattr(entity, '_original_image'):
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
    RECOVERY state: Orange/yellow pulse + shield bubble overlay.
    Shield blinks rapidly at end to warn player.
    """
    # Cache base image
    if not hasattr(entity, "_base_image") or entity._base_image is None:
        entity._base_image = entity.image.copy()

    base = entity._base_image
    elapsed = entity.anim_context.get("elapsed_time", 0)

    # === Player tint: pulsing orange/yellow ===
    tinted = base.copy()
    pulse = 0.5 + 0.5 * math.sin(elapsed * 4)
    orange = int(60 + 30 * pulse)
    yellow = int(30 + 20 * pulse)
    tinted.fill((orange, yellow, 0), special_flags=pygame.BLEND_RGB_ADD)

    # === Shield bubble overlay ===
    shield_visible = True

    # Warning phase: rapid blink in last 30%
    if t > 0.7:
        blink_rate = 0.08
        shield_visible = int(elapsed / blink_rate) % 2 == 0

    if shield_visible:
        _draw_shield_bubble(tinted, alpha=80 + int(40 * pulse))

    entity.image = tinted

    # Emit occasional shield particles
    ctx = entity.anim_context
    particle_key = int(elapsed * 8)
    if particle_key % 4 == 0 and ctx.get("_last_particle_time", -1) != particle_key:
        ctx["_last_particle_time"] = particle_key
        ParticleEmitter.burst("shield_shimmer", entity.rect.center, count=2)

    # Cleanup at end
    if t >= 1.0:
        entity.image = entity._base_image.copy()
        entity.image.set_alpha(255)
        if hasattr(entity, '_base_image'):
            del entity._base_image


def _draw_shield_bubble(surface, alpha=100, color=(100, 200, 255)):
    """
    Draw a shield bubble overlay on a surface.
    Reusable for items or other effects.
    """
    w, h = surface.get_size()
    center = (w // 2, h // 2)
    radius = max(w, h) // 2 + 16

    # Create shield surface with transparency
    shield_surf = pygame.Surface((w, h), pygame.SRCALPHA)

    # Outer glow ring
    glow_color = (*color, alpha // 3)
    pygame.draw.circle(shield_surf, glow_color, center, radius + 2, 4)

    # Main shield ring
    ring_color = (*color, alpha)
    pygame.draw.circle(shield_surf, ring_color, center, radius, 2)

    # Inner highlight
    highlight_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50), alpha // 2)
    pygame.draw.circle(shield_surf, highlight_color, center, radius - 3, 1)

    surface.blit(shield_surf, (0, 0))
