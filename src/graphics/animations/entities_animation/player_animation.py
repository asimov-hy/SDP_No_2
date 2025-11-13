"""
player.py
---------
Player-specific animation definitions (Tier 2).

All player animations centralized here for easy tuning.
"""

from ..animation_effects.death_animation import death_fade
from ..animation_effects.damage_animation import damage_flash


# ============================================================
# Death Animations
# ============================================================

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

def damage_player(entity, t):
    """
    Standard damage feedback: quick red flash.
    Duration: 0.15s recommended
    """
    return damage_flash(entity, t)


def invuln_blink(entity, t):
    """
    Invulnerability visual: alpha blink.
    Duration: match invuln time (typically 1.0-2.0s)

    Usage:
        self.anim.play(invuln_blink, duration=self.invuln_time)
    """
    # Blink 4 times during invulnerability
    import math
    alpha = int(255 * (0.3 + 0.7 * abs(math.sin(t * 4 * math.pi))))
    entity.image.set_alpha(alpha)