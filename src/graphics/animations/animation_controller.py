class AnimationController:
    __slots__ = ('active_func', 'timer', 'duration', 'entity')
    
    def __init__(self):
        self.active_func = None
        self.timer = 0.0
        self.duration = 0.0
        self.entity = None
    
    def play(self, anim_func, duration=1.0):
        self.active_func = anim_func
        self.timer = 0.0
        self.duration = duration
    
    def update(self, entity, dt):
        if not self.active_func:
            return False
        
        self.timer += dt
        t = min(1.0, self.timer / self.duration)
        
        self.active_func(entity, t)
        
        if t >= 1.0:
            self.active_func = None
            return True
        return False