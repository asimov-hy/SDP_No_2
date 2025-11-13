# In animation_controller.py - add registry and context
class AnimationController:
    __slots__ = ('active_func', 'timer', 'duration', 'entity', 'context')

    def __init__(self):
        self.active_func = None
        self.timer = 0.0
        self.duration = 0.0
        self.entity = None
        self.context = {}  # for passing params to animations

    def play(self, anim_func, duration=1.0, **kwargs):
        self.active_func = anim_func
        self.timer = 0.0
        self.duration = duration
        self.context = {
            "duration": duration,
            "elapsed_time": 0.0,
            **kwargs
        }

    def update(self, entity, dt):
        if not self.active_func:
            return False

        self.timer += dt
        t = min(1.0, self.timer / self.duration)

        # Update elapsed time in context
        self.context["elapsed_time"] = self.timer

        # Make context accessible to entity
        entity.anim_context = self.context

        self.active_func(entity, t)

        if t >= 1.0:
            self.active_func = None

            if "target_state" in self.context:
                _apply_visual_state(entity, self.context["target_state"])

            return True
        return False

registry = {}

def register(tag: str, anim_class):
    """Register animation handler for entity collision_tag."""
    registry[tag] = anim_class


def _apply_visual_state(entity, state_key):
    """Apply visual state change after animation completes."""
    if hasattr(entity, "render_mode"):
        if entity.render_mode == "shape":
            # Use base entity helper instead of _color_cache
            new_color = entity.get_target_color(state_key)
            entity.refresh_visual(new_color=new_color)
        else:
            # Use base entity helper instead of _image_cache
            new_image = entity.get_target_image(state_key)
            if new_image:
                entity.refresh_visual(new_image=new_image)

        # Update current state tracker
        entity._current_visual_state = state_key
