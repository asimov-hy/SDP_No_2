"""
animation_player.py
-------------------
Defines the Player's specific animation behaviors.

Responsibilities
----------------
- Provide visual-only feedback animations for player actions.
- Use animation utility modules for modular, composable effects.
- Ensure all animations are fail-safe and never affect physics or logic.

Supported Animations
--------------------
- dodge: Spin with ease-in-out speed profile.
- dash: (Future) Trail effect using particles.
- damage: (Deferred) Visual blinking handled in combat system.
- die: Fade-out and shrink effect with optional shake.
"""

import math
from src.core.utils.debug_logger import DebugLogger

# Animation utilities
from src.graphics.animations.animation_utils.anim_visual import fade_out, scale_down
from src.graphics.animations.animation_utils.anim_motion import spin_visual, shake_position, tilt
from src.graphics.animation_registry import register


@register("player")
class AnimationPlayer:
    """Defines Player-specific animation sequences."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, entity):
        """
        Bind the animation controller to the player entity.

        Args:
            entity: The Player entity to animate.
        """
        self.entity = entity
        self.alive = True

        DebugLogger.state("AnimationPlayer initialized", category="effects")

    # ===========================================================
    # Dodge Animation
    # ===========================================================
    def dodge(self, t: float):
        """
        Performs a spin-dodge animation:
        - Rotates the sprite with a smooth ease-in-out timing curve.
        - Adds subtle tilt for depth.
        - Visual-only; does not alter position or hitbox.

        Args:
            t (float): Normalized time (0.0 → 1.0)
        """
        try:
            # Ease-in-out curve for rotation speed
            eased_t = 0.5 - 0.5 * math.cos(math.pi * t)

            # Smooth spin based on eased progress
            spin_visual(self.entity, eased_t, total_angle=360)

            # Optional: small tilt to emphasize direction
            tilt(self.entity, eased_t, max_angle=10)

        except Exception as e:
            DebugLogger.warn(f"[AnimationPlayer.dodge] Failed: {e}", category="animation")

    # ===========================================================
    # Dash Animation (placeholder)
    # ===========================================================
    def dash(self, t: float):
        """
        Placeholder: Player dash animation (to be paired with particle trails).
        Planned Features:
        - Motion streak / afterimage trail.
        - Subtle fade / blur.
        - Small positional wobble for energy.
        """
        pass

    # ===========================================================
    # Take Damage Animation (reference only)
    # ===========================================================
    def damage(self, t: float):
        """
        Placeholder: Handled by PlayerCombat blinking logic.
        Included here for structural completeness.
        """
        try:
            entity = self.entity

            # 1) Blink frequency (controls how often player flickers)
            blink_interval = 0.15  # seconds between visibility toggles
            blink_phase = int((t * entity.invuln_duration) / blink_interval) % 2

            # 2) Flash white at impact
            if t < 0.1:
                entity.image.fill((255, 255, 255))
                entity.visible = True

            # 3) Blink during invulnerability
            else:
                entity.visible = blink_phase == 0

            # 4) Ensure fade-out of flicker near the end
            if t > 0.9:
                entity.visible = True

        except Exception as e:
            DebugLogger.warn(f"[AnimationPlayer.damage] Failed: {e}", category="animation")

    # ===========================================================
    # Death Animation
    # ===========================================================
    def die(self, t: float):
        """
        Player death animation sequence:
        - Fade-out while scaling down.
        - Optional mild shake for visual impact.
        - Purely visual; entity removal handled elsewhere.

        Args:
            t (float): Normalized time (0.0 → 1.0)
        """
        pass
        # try:
        #     # Combine smooth fade and scale
        #     fade_out(self.entity, t)
        #     scale_down(self.entity, t, factor=0.2)
        #
        #     # Add subtle shake near the beginning
        #     if t < 0.5:
        #         shake_position(self.entity, t, intensity=4)
        #
        # except Exception as e:
        #     DebugLogger.warn(f"[AnimationPlayer.die] Failed: {e}", category="animation")
