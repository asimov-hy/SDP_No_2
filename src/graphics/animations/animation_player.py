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

from src.core.debug.debug_logger import DebugLogger

# Animation utilities
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
        print("dodge animation")

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
    def intangible(self, t: float):
        """
        when player is intangible - either taken damage or possible item
        """
        print("damage animation")

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
        print("death animation")
