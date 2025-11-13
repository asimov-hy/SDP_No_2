"""
animation_manager.py
--------------------
Centralized system responsible for managing all entity animations.

Responsibilities
----------------
- Manage animation playback, timing, and synchronization per entity.
- Dynamically resolve animation handlers using a shared registry system.
- Provide a consistent interface for starting, updating, and stopping animations.
- Guarantee fail-safety — animation errors never crash the main game loop.
- Support in-animation effect triggers (e.g., particles, sounds, flashes).
"""

from src.core.debug.debug_logger import DebugLogger
from src.graphics.animations.animation_controller import registry


class AnimationManager:
    """Global animation controller handling per-entity animation execution."""

    # ===========================================================
    # Initialization
    # ===========================================================
    def __init__(self, entity):
        """
        Initialize an AnimationManager for a given entity.

        Args:
            entity: The entity instance this manager will control animations for.
        """
        self.entity = entity
        self.animations = self._resolve_animation_class(entity)

        # -------------------------------------------------------
        # Playback state
        # -------------------------------------------------------
        self.active_type = None     # Current animation name
        self.timer = 0.0            # Time elapsed since start
        self.duration = 0.0         # Total animation duration
        self.finished = False       # Completion flag

        # -------------------------------------------------------
        # Control flags and callback
        # -------------------------------------------------------
        self.enabled = True         # Allows disabling animations globally per entity
        self.on_complete = None     # Optional completion callback (e.g., re-enable hitbox)
        self._effect_queue = []     # Holds animation_effects scheduled to trigger during playback

        DebugLogger.init(
            f"AnimationManager initialized for {type(entity).__name__}",
            category="animation"
        )

    # ===========================================================
    # Animation Resolver
    # ===========================================================
    def _resolve_animation_class(self, entity):
        """
        Retrieve the appropriate animation handler from the registry.

        The registry maps entity collision tags to animation handler classes.
        Example: "player" → AnimationPlayer, "enemy_straight" → AnimationEnemyStraight

        Returns:
            Instance of the matching animation class, or None if unregistered.
        """
        tag = getattr(entity, "collision_tag", "")
        anim_class = registry.get(tag)

        if anim_class:
            DebugLogger.state(f"Resolved animation handler for '{tag}'", category="animation")
            return anim_class(entity)

        DebugLogger.warn(f"No registered animation handler for '{tag}'", category="animation")
        return None

    # ===========================================================
    # Playback Controls
    # ===========================================================
    def play(self, anim_type: str, duration: float = 1.0):
        """
        Start an animation sequence for this entity.

        Args:
            anim_type (str): Name of the animation to play (e.g., "damage_blink", "death").
            duration (float): Total time the animation should last in seconds.
        """
        if not self.enabled:
            return

        # Lazy resolve only when needed
        if not self.animations:
            self.animations = self._resolve_animation_class(self.entity)

        self.active_type = anim_type
        self.timer = 0.0
        self.duration = duration
        self.finished = False
        self._effect_queue.clear()

        DebugLogger.state(
            f"{type(self.entity).__name__}: Animation '{anim_type}' started ({duration:.2f}s)",
            category="animation"
        )

    def stop(self):
        """Immediately stop the current animation and reset playback state."""
        if self.active_type:
            DebugLogger.state(
                f"{type(self.entity).__name__}: Animation '{self.active_type}' stopped",
                category="animation"
            )

        self.active_type = None
        self.timer = 0.0
        self.duration = 0.0
        self.finished = True
        self.on_complete = None
        self._effect_queue.clear()

    # ===========================================================
    # Effect Integration
    # ===========================================================
    def bind_effect(self, trigger_time: float, effect):
        """
        Schedule an effect to fire once during the active animation.

        Args:
            trigger_time (float): Normalized time (0.0–1.0) when effect should occur.
            effect (Callable | str): Function or named effect to trigger.
                                     If str, it will call entity.effect_manager.trigger(name).
        """
        trigger_time = max(0.0, min(trigger_time, 1.0))
        self._effect_queue.append({
            "trigger": trigger_time,
            "effect": effect,
            "fired": False,
        })
        DebugLogger.state(
            f"[BindEffect] {type(self.entity).__name__}: '{effect}' @ t={trigger_time}",
            category="animation"
        )

    def _check_effect_triggers(self, t: float):
        """Execute any animation_effects whose trigger times have been reached."""
        for fx in list(self._effect_queue):
            if not fx["fired"] and t >= fx["trigger"]:
                fx["fired"] = True
                eff = fx["effect"]

                try:
                    if callable(eff):
                        eff(self.entity)
                    elif isinstance(eff, str):
                        if hasattr(self.entity, "effect_manager"):
                            self.entity.status_manager.trigger(eff)
                        else:
                            DebugLogger.warn(
                                f"[EffectSkip] {self.entity.collision_tag} has no effect_manager for '{eff}'",
                                category="animation_effects"
                            )
                except Exception as e:
                    DebugLogger.warn(
                        f"[EffectFail] {eff} on {self.entity.collision_tag} → {e}",
                        category="animation_effects"
                    )

    # ===========================================================
    # Update Loop
    # ===========================================================
    def update(self, dt: float):
        """
        Advance the animation timeline and execute its bound behavior.

        Args:
            dt (float): Delta time (seconds) since the last frame.
        """
        if not self.enabled or not getattr(self.entity, "alive", True):
            return
        if not self.active_type or not self.animations:
            return

        try:
            # -------------------------------------------------------
            # 1) Advance animation progress and normalize to [0.0, 1.0]
            # -------------------------------------------------------
            self.timer += dt
            t = min(1.0, self.timer / max(self.duration, 1e-6))  # Avoid division by zero

            # -------------------------------------------------------
            # 2) Execute the animation method if defined
            # -------------------------------------------------------
            method = getattr(self.animations, self.active_type, None)
            if callable(method):
                method(t)
                # Fire queued animation_effects when appropriate
                self._check_effect_triggers(t)
            else:
                DebugLogger.warn(
                    f"{type(self.entity).__name__}: Unknown animation '{self.active_type}'",
                    category="animation"
                )
                self.stop()
                return

            # -------------------------------------------------------
            # 3) Stop when finished and trigger optional callback
            # -------------------------------------------------------
            if t >= 1.0:
                if callable(self.on_complete):
                    try:
                        self.on_complete(self.entity, self.active_type)
                    except Exception as e:
                        DebugLogger.warn(
                            f"Animation '{self.active_type}' callback failed → {e}",
                            category="animation"
                        )
                self.stop()

        except Exception as e:
            # -------------------------------------------------------
            # 4) Fail-safe: gracefully stop faulty animations
            # -------------------------------------------------------
            DebugLogger.warn(
                f"{type(self.entity).__name__}: Animation '{self.active_type}' failed → {e}",
                category="animation"
            )
            self.stop()

    # ===========================================================
    # Utility
    # ===========================================================
    def has(self, anim_type: str) -> bool:
        """Return True if the entity supports the given animation."""
        return callable(getattr(self.animations, anim_type, None))
