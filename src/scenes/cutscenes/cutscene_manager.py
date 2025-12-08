"""
cutscene_manager.py
-------------------
Orchestrates cutscene action sequences.
"""

from typing import List, Callable, Optional
from .cutscene_action import CutsceneAction


class CutsceneManager:
    """Manages cutscene playback."""

    def __init__(self):
        self.actions: List[CutsceneAction] = []
        self.current_index = 0
        self.playing = False
        self.on_complete: Optional[Callable] = None

    def play(self, actions: List[CutsceneAction], on_complete: Callable = None):
        """Start a cutscene sequence."""
        self.actions = actions
        self.current_index = 0
        self.playing = True
        self.on_complete = on_complete

        if actions:
            actions[0].on_start()

    def skip(self):
        """Skip to end of cutscene."""
        if self.playing:
            # Run all remaining on_end callbacks
            for i in range(self.current_index, len(self.actions)):
                self.actions[i].on_end()
            self._finish()

    def update(self, dt: float) -> bool:
        """Update current action. Returns True while playing."""
        if not self.playing:
            return False

        action = self.actions[self.current_index]

        if action.update(dt):
            action.on_end()
            self.current_index += 1

            if self.current_index >= len(self.actions):
                self._finish()
            else:
                self.actions[self.current_index].on_start()

        return self.playing

    def draw(self, draw_manager):
        """Draw current action visuals."""
        if self.playing and self.current_index < len(self.actions):
            self.actions[self.current_index].draw(draw_manager)

    def _finish(self):
        """Complete cutscene."""
        self.playing = False
        if self.on_complete:
            self.on_complete()

    @property
    def is_playing(self) -> bool:
        return self.playing
