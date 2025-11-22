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
- Support in-animation effects triggers (e.g., particles, sounds, flashes).
"""

from src.core.debug.debug_logger import DebugLogger
from src.graphics.animations.animation_registry import get_animation, get_animations_for_entity


class AnimationManager:
    """Global animation controller handling per-entity animation execution."""

    __slots__ = (
        'entity',  # Entity being animated
        'active_type',  # Current animation name
        'timer',  # Elapsed time
        'duration',  # Total animation duration
        'finished',  # Completion flag
        'enabled',  # Global enable/disable
        'on_complete',  # Completion callback
        '_effect_queue',  # Scheduled effects
        'context'  # Animation parameters dict
    )

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

        # Playback state
        self.active_type = None
        self.timer = 0.0
        self.duration = 0.0
        self.finished = False

        # Control flags and callback
        self.enabled = True
        self.on_complete = None
        self._effect_queue = []

        # Animation context (passed to animation functions)
        self.context = {}

        # Debug: Log available animations for this entity
        category = getattr(entity, "category", "unknown")
        anims = get_animations_for_entity(category)
        if anims:
            DebugLogger.init(
                f"AnimationManager for {type(entity).__name__} (category: {category}) - {len(anims)} animations available",
                category="animation"
            )
        # else:
        #     DebugLogger.warn(
        #         f"AnimationManager for {type(entity).__name__} (tag: {tag}) - NO animations registered",
        #         category="animation"
        #     )

    # ===========================================================
    # Playback Controls
    # ===========================================================
    def play(self, anim_type: str, duration: float = 1.0, **kwargs):
        """
        Start an animation sequence for this entity.

        Args:
            anim_type (str): Name of the animation to play (e.g., "damage", "death").
            duration (float): Total time the animation should last in seconds.
            **kwargs: Additional parameters passed to animation function via context.
                      Common params: blink_interval, target_state, previous_state
        """
        if not self.enabled:
            return

        self.active_type = anim_type
        self.timer = 0.0
        self.duration = duration
        self.finished = False
        self._effect_queue.clear()

        # Store original image once at animation start (cold path)
        if hasattr(self.entity, 'image') and self.entity.image:
            self.entity._original_image = self.entity.image.copy()

        # Build context for animation function
        self.context = {
            "duration": duration,
            "elapsed_time": 0.0,
            **kwargs
        }

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

        # Restore original image if stored
        if hasattr(self.entity, '_original_image') and self.entity._original_image:
            self.entity.image = self.entity._original_image
            self.entity.image.set_alpha(255)

        self.active_type = None
        self.timer = 0.0
        self.duration = 0.0
        self.finished = True
        self.on_complete = None
        self._effect_queue.clear()

    # ===========================================================
    # effects Integration
    # ===========================================================
    def bind_effect(self, trigger_time: float, effect):
        """
        Schedule an effects to fire once during the active animation.

        Args:
            trigger_time (float): Normalized time (0.0–1.0) when effects should occur.
            effect (Callable | str): Function or named effects to trigger.
                                     If str, it will call entity.effect_manager.trigger(name).
        """
        trigger_time = max(0.0, min(trigger_time, 1.0))
        self._effect_queue.append({
            "trigger": trigger_time,
            "effects": effect,
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
                eff = fx["effects"]

                try:
                    if callable(eff):
                        eff(self.entity)
                    elif isinstance(eff, str):
                        if hasattr(self.entity, "effect_manager"):
                            self.entity.state_manager.timed_state(eff)
                        else:
                            DebugLogger.warn(
                                f"[EffectSkip] {self.entity.category} has no effect_manager for '{eff}'",
                                category="animation_effects"
                            )
                except Exception as e:
                    DebugLogger.warn(
                        f"[EffectFail] {eff} on {self.entity.category} → {e}",
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
        if not self.active_type:
            return

        try:
            # Advance animation progress
            self.timer += dt
            t = min(1.0, self.timer / max(self.duration, 1e-6))

            # Update context with current elapsed time
            self.context["elapsed_time"] = self.timer

            # Make context accessible to entity (for animation functions)
            self.entity.anim_context = self.context

            # Lookup animation function from registry
            anim_func = get_animation(self.entity.category, self.active_type)

            if anim_func:
                anim_func(self.entity, t)
                self._check_effect_triggers(t)
            else:
                DebugLogger.warn(
                    f"{type(self.entity).__name__}: No animation '{self.active_type}' registered for category '{self.entity.category}'",
                    category="animation"
                )
                self.stop()
                return

            # Stop when finished and trigger callback
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
                return True

        except Exception as e:
            # Fail-safe: gracefully stop faulty animations
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
        return get_animation(self.entity.category, anim_type) is not None
