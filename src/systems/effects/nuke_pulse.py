"""
nuke_pulse.py
-------------
Expanding pulse that freezes entities, then detonates them.
"""

import math
import random
import pygame

from src.core.runtime.game_settings import Display, Layers
from src.core.debug.debug_logger import DebugLogger
from src.core.services.event_manager import get_events, ScreenShakeEvent, BulletClearEvent, SpawnPauseEvent
from src.entities.entity_state import InteractionState, LifecycleState
from src.entities.entity_types import EntityCategory
from src.graphics.particles.particle_manager import ParticleEmitter


class PulseState:
    EXPANDING = 0
    FADING = 1
    DETONATING = 2
    DONE = 3


class NukePulse:
    """Expanding ring that freezes enemies, then detonates them."""

    def __init__(self, center, start_speed=1600, end_speed=200, fade_duration=0.3,
                 detonate_duration=0.5, damage=9999,
                 max_explosion_delay=0.4, min_explosion_delay=0.03, explosion_decay=0.85,
                 color=(255, 255, 150), ring_width=12,
                 target_category=EntityCategory.ENEMY):
        """
        Args:
            center: (x, y) origin point
            start_speed: Initial expansion speed (pixels per second)
            end_speed: Final expansion speed (pixels per second)
            fade_duration: Seconds to fade after max radius
            detonate_duration: Seconds of shake before explode
            damage: Damage dealt on detonation
            color: RGB tuple for ring
            ring_width: Thickness of ring
            target_category: Which entities to affect
        """
        self.center = center
        self.radius = 0
        self.start_speed = start_speed
        self.end_speed = end_speed
        self.max_radius = math.hypot(Display.WIDTH, Display.HEIGHT) * 0.6

        self.damage = damage
        self.color = color
        self.ring_width = ring_width
        self.alpha = 255
        self.target_category = target_category

        self.fade_duration = fade_duration
        self.detonate_duration = detonate_duration
        self.max_explosion_delay = max_explosion_delay
        self.min_explosion_delay = min_explosion_delay
        self.explosion_decay = explosion_decay

        self._explosion_times = []  # Pre-calculated explosion times

        self.state = PulseState.EXPANDING
        self._state_timer = 0.0
        self._detonate_timer = 0.0
        self._detonate_index = 0

        self._frozen_entities = []
        self._original_positions = {}

        # Pause spawning during nuke
        get_events().dispatch(SpawnPauseEvent(paused=True))

        DebugLogger.action("Nuke pulse expanding...", category="effects")

    @property
    def active(self):
        return self.state != PulseState.DONE

    def update(self, dt, entities):
        """Update pulse based on current state."""
        if self.state == PulseState.EXPANDING:
            self._update_expanding(dt, entities)
        elif self.state == PulseState.FADING:
            self._update_fading(dt)
        elif self.state == PulseState.DETONATING:
            self._update_detonating(dt)

    def _update_expanding(self, dt, entities):
        """Expand ring and freeze entities on contact."""
        # Exponential slowdown: fast at start, slow at end
        progress = self.radius / self.max_radius  # 0.0 -> 1.0
        current_speed = self.start_speed * math.pow(self.end_speed / self.start_speed, progress)
        self.radius += current_speed * dt

        for entity in entities:
            # Filter by category
            if getattr(entity, 'category', None) != self.target_category:
                continue
            if getattr(entity, 'death_state', LifecycleState.DEAD) != LifecycleState.ALIVE:
                continue
            if entity in self._frozen_entities:
                continue

            # Distance check - hit if inside current radius
            dist = math.hypot(
                entity.rect.centerx - self.center[0],
                entity.rect.centery - self.center[1]
            )

            if dist <= self.radius:
                self._freeze_entity(entity)

        # Clear enemy bullets inside expanding ring
        get_events().dispatch(BulletClearEvent(
            center=self.center,
            radius=self.radius,
            owner="enemy"
        ))

        # Transition when fully expanded
        if self.radius >= self.max_radius:
            self.state = PulseState.FADING
            self._state_timer = 0.0
            DebugLogger.action(
                f"Pulse fading, {len(self._frozen_entities)} frozen",
                category="effects"
            )

    def _update_fading(self, dt):
        """Fade out the ring."""
        self._state_timer += dt
        progress = self._state_timer / self.fade_duration
        self.alpha = int(255 * (1.0 - progress))

        if self._state_timer >= self.fade_duration:
            self.state = PulseState.DETONATING
            self._state_timer = 0.0
            self._detonate_index = 0

            # Shuffle for random explosion order
            random.shuffle(self._frozen_entities)

            # Pre-calculate explosion times (accelerating curve)
            self._explosion_times = self._generate_explosion_times(len(self._frozen_entities))

            DebugLogger.action("Nuke detonation starting...", category="effects")

    def _update_detonating(self, dt):
        """Shake frozen entities, explode one by one."""
        self._state_timer += dt

        # Shake remaining frozen entities
        shake_intensity = 4
        for entity in self._frozen_entities[self._detonate_index:]:
            if getattr(entity, 'death_state', LifecycleState.DEAD) != LifecycleState.ALIVE:
                continue

            orig_pos = self._original_positions.get(id(entity))
            if orig_pos:
                offset_x = random.uniform(-shake_intensity, shake_intensity)
                offset_y = random.uniform(-shake_intensity, shake_intensity)
                entity.pos.x = orig_pos[0] + offset_x
                entity.pos.y = orig_pos[1] + offset_y
                entity.sync_rect()

        # Explode entities when their scheduled time arrives
        while (self._detonate_index < len(self._frozen_entities) and
               self._state_timer >= self._explosion_times[self._detonate_index]):
            self._detonate_single(self._detonate_index)
            self._detonate_index += 1

        # Done when all exploded
        if self._detonate_index >= len(self._frozen_entities):
            self._finish_detonation()
            self.state = PulseState.DONE

    def _freeze_entity(self, entity):
        """Freeze an entity in place."""
        self._frozen_entities.append(entity)
        self._original_positions[id(entity)] = (entity.pos.x, entity.pos.y)
        entity.state = InteractionState.FROZEN

        # Visual feedback
        ParticleEmitter.burst("damage", entity.rect.center, count=4)

    def _generate_explosion_times(self, count):
        """Generate explosion times with exponentially decreasing gaps."""
        if count == 0:
            return []
        if count == 1:
            return [self.detonate_duration]

        times = []
        current_time = self.detonate_duration
        current_delay = self.max_explosion_delay

        for i in range(count):
            times.append(current_time)
            # Exponential decay, but respect minimum
            current_time += current_delay
            current_delay = max(current_delay * self.explosion_decay, self.min_explosion_delay)

        return times

    def _detonate_single(self, index):
        """Explode a single frozen entity."""
        entity = self._frozen_entities[index]

        if getattr(entity, 'death_state', LifecycleState.DEAD) != LifecycleState.ALIVE:
            return

        # Restore position
        orig_pos = self._original_positions.get(id(entity))
        if orig_pos:
            entity.pos.x, entity.pos.y = orig_pos
            entity.sync_rect()

        # Particle burst
        ParticleEmitter.burst("enemy_explode", entity.rect.center, count=20)

        # Kill
        entity.take_damage(self.damage, source="nuke")

    def _finish_detonation(self):
        """Cleanup after all entities detonated."""
        # Screen shake at end
        get_events().dispatch(ScreenShakeEvent(intensity=15, duration=0.4))

        DebugLogger.action(
            f"Nuke detonated {len(self._frozen_entities)} enemies!",
            category="effects"
        )

        self._frozen_entities.clear()
        self._original_positions.clear()

        # Resume spawning
        get_events().dispatch(SpawnPauseEvent(paused=False))

    def draw(self, draw_manager):
        """Draw expanding/fading ring."""
        if self.state in (PulseState.DONE, PulseState.DETONATING):
            return

        if self.radius <= 0:
            return

        size = int(self.radius * 2) + self.ring_width * 2
        if size <= 0:
            return

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2

        color_with_alpha = (*self.color[:3], self.alpha)

        if self.radius > self.ring_width:
            pygame.draw.circle(
                surf, color_with_alpha,
                (center, center),
                int(self.radius),
                self.ring_width
            )

        rect = surf.get_rect(center=self.center)
        draw_manager.queue_draw(surf, rect, layer=Layers.EFFECTS if hasattr(Layers, 'EFFECTS') else 50)