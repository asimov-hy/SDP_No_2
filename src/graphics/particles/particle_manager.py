"""
particle_manager.py
------------------
Lightweight particle system with pre-rendered sprites for optimal performance.

Usage:
    # Ambient overlay (embers, rain)
    embers = ParticleOverlay("ember")
    embers.update(dt)
    embers.render(surface)

    # Entity-attached emitter (fire trail)
    trail = ParticleEmitter("fire_trail")
    trail.emit(enemy.pos)
    trail.update(dt)
    trail.render(surface)

    # One-shot burst (damage particles)
    ParticleEmitter.burst("damage", position, count=8)
"""

import pygame
import random
import math

from src.core.runtime.game_settings import Display, Layers, Debug
from src.core.services.config_manager import load_config


# ===========================================================
# Load Presets from JSON
# ===========================================================


def _load_presets():
    """Load particle presets from config, convert lists to tuples."""
    data = load_config("particles.json", default_dict={})

    # Convert color lists to tuples (JSON can't store tuples)
    for preset in data.values():
        if "colors" in preset:
            preset["colors"] = [tuple(c) for c in preset["colors"]]
        if "size_range" in preset:
            preset["size_range"] = tuple(preset["size_range"])
        if "speed_range" in preset:
            preset["speed_range"] = tuple(preset["speed_range"])
        if "lifetime" in preset:
            preset["lifetime"] = tuple(preset["lifetime"])
        if "direction" in preset:
            preset["direction"] = tuple(preset["direction"])

    return data


PARTICLE_PRESETS = _load_presets()


# ===========================================================
# Pre-rendered Sprite Cache
# ===========================================================


class SpriteCache:
    """Pre-renders particle sprites for fast blitting."""

    _cache = {}

    @classmethod
    def get_sprite(cls, color, size, glow=False, shape="circle"):
        """Get or create cached particle sprite."""
        key = (color, size, glow, shape)
        if key not in cls._cache:
            cls._cache[key] = cls._create_sprite(color, size, glow, shape)
        return cls._cache[key]

    @classmethod
    def _create_sprite(cls, color, size, glow, shape="circle"):
        """Create a single particle sprite."""
        if glow:
            # Larger surface for glow effect
            surf_size = size * 3
            surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center = surf_size // 2

            # Outer glow (low alpha)
            glow_color = (*color, 40)
            if shape == "square":
                pygame.draw.rect(
                    surf,
                    glow_color,
                    (
                        center - size - 2,
                        center - size - 2,
                        (size + 2) * 2,
                        (size + 2) * 2,
                    ),
                )
                pygame.draw.rect(
                    surf,
                    (*color, 255),
                    (center - size, center - size, size * 2, size * 2),
                )
            else:
                pygame.draw.circle(surf, glow_color, (center, center), size + 2)
                pygame.draw.circle(surf, (*color, 255), (center, center), size)
        else:
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            if shape == "square":
                pygame.draw.rect(surf, (*color, 255), (0, 0, size * 2, size * 2))
            else:
                pygame.draw.circle(surf, (*color, 255), (size, size), size)

        return surf

    @classmethod
    def clear(cls):
        """Clear cache (call on scene change if needed)."""
        cls._cache.clear()


# ===========================================================
# Single Particle
# ===========================================================


class Particle:
    """Individual particle with position, velocity, and lifetime."""

    __slots__ = (
        "x",
        "y",
        "vx",
        "vy",
        "size",
        "max_size",
        "color",
        "lifetime",
        "max_lifetime",
        "alpha",
        "glow",
        "shrink",
        "grow",
        "fade_delay",
    )

    def __init__(
        self,
        x,
        y,
        vx,
        vy,
        size,
        color,
        lifetime,
        glow=False,
        shrink=False,
        grow=False,
        fade_delay=0.0,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.max_size = size
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.alpha = 255
        self.glow = glow
        self.shrink = shrink
        self.grow = grow
        self.fade_delay = fade_delay

    def update(self, dt, wobble=0, spread_growth=1.0):
        """Update particle position and lifetime."""
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Wobble (horizontal drift)
        if wobble:
            age = 1.0 - (self.lifetime / self.max_lifetime)
            wobble_mult = 1.0 + (age * spread_growth)
            self.x += random.uniform(-wobble, wobble) * wobble_mult * dt

        self.lifetime -= dt

        # Fade alpha based on remaining lifetime (respecting fade_delay)
        t = max(0, self.lifetime / self.max_lifetime)
        if t > self.fade_delay:
            self.alpha = 255
        else:
            self.alpha = int(255 * (t / self.fade_delay)) if self.fade_delay > 0 else 0

        # Size changes
        if self.shrink:
            self.size = max(1, int(self.max_size * t))
        elif self.grow:
            self.size = int(self.max_size * (1 + (1 - t) * 0.5))

        return self.lifetime > 0

    @property
    def alive(self):
        return self.lifetime > 0


# ===========================================================
# Debris Particle (bouncing ground particles)
# ===========================================================


class DebrisParticle:
    """Particle with gravity and bounce behavior for ground shake effects."""

    __slots__ = (
        "x",
        "y",
        "vx",
        "vy",
        "spawn_y",
        "size",
        "color",
        "lifetime",
        "gravity",
        "bounce_damping",
        "min_velocity",
        "active",
    )

    def __init__(
        self,
        x,
        y,
        vx,
        vy,
        size,
        color,
        lifetime,
        gravity=800,
        bounce_damping=0.3,
        min_velocity=10,
    ):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.spawn_y = y  # Remember ground level
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.gravity = gravity
        self.bounce_damping = bounce_damping  # 30% velocity retained
        self.min_velocity = min_velocity  # Stop bouncing below this
        self.active = True

    def update(self, dt):
        """Update with gravity and bounce logic."""
        if not self.active:
            return False

        # Apply gravity
        self.vy += self.gravity * dt

        # Move
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Bounce check: hit ground (at or below spawn_y) while moving down
        if self.y >= self.spawn_y and self.vy > 0:
            self.y = self.spawn_y  # Snap to ground

            # Check if velocity is strong enough to bounce
            if abs(self.vy) > self.min_velocity:
                self.vy = -self.vy * self.bounce_damping
                self.vx *= 0.8  # Slight horizontal friction
            else:
                # Too slow, stop bouncing
                self.vy = 0
                self.vx = 0

        # Lifetime countdown
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False

        return self.active


# ===========================================================
# Particle Emitter (for entity trails, bursts)
# ===========================================================


class ParticleEmitter:
    """
    Spawns particles from a position.
    Use for fire trails, damage bursts, etc.
    """

    # Class-level particle pool for all emitters
    _active_particles = []
    _particle_limit = 500

    def __init__(self, preset_name, emit_rate=30):
        """
        Args:
            preset_name: Key from PARTICLE_PRESETS
            emit_rate: Particles per second (for continuous emission)
        """
        self.preset = PARTICLE_PRESETS.get(preset_name, PARTICLE_PRESETS["damage"])
        self.emit_rate = emit_rate
        self.emit_timer = 0
        self.active = True

    def emit(self, pos, direction=None, count=1):
        """
        Emit particles at position.

        Args:
            pos: (x, y) tuple or pygame.Vector2
            direction: Override direction (for trails behind moving entity)
            count: Number of particles to spawn
        """
        if not self.active:
            return

        preset = self.preset

        for _ in range(count):
            if (
                len(ParticleEmitter._active_particles)
                >= ParticleEmitter._particle_limit
            ):
                break

            # Random properties from preset
            color = random.choice(preset["colors"])
            size = random.randint(*preset["size_range"])
            speed = random.uniform(*preset["speed_range"])
            lifetime = random.uniform(*preset["lifetime"])

            # Direction with spread
            base_dir = direction or preset.get("direction") or (0, 0)
            spread = preset.get("spread", 0)

            if spread == 360:
                # Radial burst
                angle = random.uniform(0, 360)
            else:
                # Cone spread
                base_angle = (
                    math.degrees(math.atan2(base_dir[1], base_dir[0]))
                    if base_dir != (0, 0)
                    else -90
                )
                angle = base_angle + random.uniform(-spread / 2, spread / 2)

            rad = math.radians(angle)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed

            particle = Particle(
                x=pos[0] if hasattr(pos, "__getitem__") else pos.x,
                y=pos[1] if hasattr(pos, "__getitem__") else pos.y,
                vx=vx,
                vy=vy,
                size=size,
                color=color,
                lifetime=lifetime,
                glow=preset.get("glow", False),
                shrink=preset.get("shrink", False),
                grow=preset.get("grow", False),
                fade_delay=preset.get("fade_delay", 0.0),
            )
            ParticleEmitter._active_particles.append(particle)

    def emit_continuous(self, pos, dt, direction=None):
        """Emit particles over time (call each frame for trails)."""
        self.emit_timer += dt
        interval = 1.0 / self.emit_rate if self.emit_rate > 0 else 1.0

        while self.emit_timer >= interval:
            self.emit(pos, direction, count=1)
            self.emit_timer -= interval

    @classmethod
    def burst(cls, preset_name, pos, count=8, direction=None):
        """One-shot particle burst (static method for convenience)."""
        emitter = cls(preset_name)
        emitter.emit(pos, direction, count)

    @classmethod
    def update_all(cls, dt):
        """Update all active particles (call once per frame)."""
        cls._active_particles = [
            p
            for p in cls._active_particles
            if p.update(dt, wobble=0)  # Wobble handled per-preset below
        ]

    @classmethod
    def render_all(cls, draw_manager, layer=Layers.PARTICLES):
        """Render all active particles (call once per frame)."""
        for p in cls._active_particles:
            sprite = SpriteCache.get_sprite(p.color, p.size, p.glow)

            if p.alpha < 255:
                sprite = sprite.copy()
                sprite.set_alpha(p.alpha)

            rect = sprite.get_rect(center=(int(p.x), int(p.y)))
            draw_manager.queue_draw(sprite, rect, layer=layer)

    @classmethod
    def clear_all(cls):
        """Clear all particles."""
        cls._active_particles.clear()

    @classmethod
    def particle_count(cls):
        """Get current active particle count."""
        return len(cls._active_particles)


# ===========================================================
# Debris Emitter (for ground shake effects)
# ===========================================================


class DebrisEmitter:
    """
    Spawns bouncing debris particles to simulate ground shake.
    Particles spawn within a rect, pop upward, and bounce back to their spawn point.
    """

    def __init__(
        self,
        emit_rate=100,
        max_particles=400,
        colors=None,
        size_range=(4, 7),
        speed_range=(150, 280),
        lifetime=0.5,
        gravity=1000,
        bounce_damping=0.6,
        min_velocity=15,
    ):
        """
        Args:
            emit_rate: Particles per second
            max_particles: Maximum concurrent particles for this emitter
            colors: List of RGB tuples (defaults to earthy browns)
            size_range: (min, max) particle size
            speed_range: (min, max) initial upward velocity
            lifetime: How long particles live
            gravity: Pull strength (higher = faster fall)
            bounce_damping: Velocity retained per bounce (0.3 = 30%)
            min_velocity: Stop bouncing below this speed
        """
        self.emit_rate = emit_rate
        self.emit_timer = 0
        self.max_particles = max_particles
        self.particles = []
        self.active = True

        # Debris settings
        self.colors = colors or [
            (139, 90, 43),
            (160, 120, 80),
            (100, 80, 60),
            (120, 100, 70),
        ]
        self.size_range = size_range
        self.speed_range = speed_range
        self.lifetime = lifetime
        self.gravity = gravity
        self.bounce_damping = bounce_damping
        self.min_velocity = min_velocity

    def emit(self, spawn_rect, count=1):
        """Emit debris particles within spawn_rect area."""
        if not self.active:
            return

        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break

            # Random spawn position anywhere within rect
            x = random.uniform(spawn_rect.left, spawn_rect.right)
            y = random.uniform(spawn_rect.top, spawn_rect.bottom)

            # Random properties
            color = random.choice(self.colors)
            size = random.randint(*self.size_range)
            speed = random.uniform(*self.speed_range)

            # Launch upward with slight horizontal drift
            vx = random.uniform(-30, 30)
            vy = -speed  # Negative = upward

            particle = DebrisParticle(
                x=x,
                y=y,
                vx=vx,
                vy=vy,
                size=size,
                color=color,
                lifetime=self.lifetime,
                gravity=self.gravity,
                bounce_damping=self.bounce_damping,
                min_velocity=self.min_velocity,
            )
            self.particles.append(particle)

    def emit_continuous(self, spawn_rect, dt):
        """Emit debris over time (call each frame)."""
        self.emit_timer += dt
        interval = 1.0 / self.emit_rate if self.emit_rate > 0 else 1.0

        while self.emit_timer >= interval:
            self.emit(spawn_rect, count=1)
            self.emit_timer -= interval

    def update(self, dt):
        """Update all particles in this emitter."""
        self.particles = [p for p in self.particles if p.update(dt)]

    def render(self, draw_manager, layer=Layers.PARTICLES):
        """Render all particles as squares."""
        for p in self.particles:
            sprite = SpriteCache.get_sprite(p.color, p.size, glow=False, shape="square")
            rect = sprite.get_rect(center=(int(p.x), int(p.y)))
            draw_manager.queue_draw(sprite, rect, layer=layer)

    def clear(self):
        """Clear all particles."""
        self.particles.clear()

    @property
    def particle_count(self):
        """Get current active particle count."""
        return len(self.particles)


# ===========================================================
# Particle Overlay (ambient effects: embers, rain)
# ===========================================================


class ParticleOverlay:
    """
    Full-screen ambient particle effect.
    Use for menu backgrounds, weather effects, etc.
    """

    def __init__(
        self,
        preset_name,
        max_particles=150,
        spawn_rate=30,
        spawn_area=None,
        direction=None,
        speed=None,
        lifetime=None,
    ):
        """
        Args:
            preset_name: Key from PARTICLE_PRESETS
            max_particles: Maximum concurrent particles
            spawn_rate: Particles per second
            spawn_area: (x, y, width, height) spawn region, None = full screen edge
            direction: (dx, dy) override, None = use preset
            speed: (min, max) override, None = use preset
        """
        self.preset = PARTICLE_PRESETS.get(preset_name, PARTICLE_PRESETS["ember"])
        self.max_particles = max_particles
        self.spawn_rate = spawn_rate
        self.spawn_timer = 0
        self.particles = []
        self.active = True

        self.width = Display.WIDTH
        self.height = Display.HEIGHT

        # Overrides
        self.spawn_area = spawn_area  # (x, y, w, h) or None
        self.direction_override = direction
        self.speed_override = speed
        self.lifetime_override = lifetime

    def update(self, dt):
        """Update overlay particles."""
        if not self.active:
            return

        preset = self.preset
        wobble = preset.get("wobble", 0)

        # Update existing particles
        self.particles = [p for p in self.particles if p.update(dt, wobble)]

        # Spawn new particles
        self.spawn_timer += dt
        interval = 1.0 / self.spawn_rate if self.spawn_rate > 0 else 1.0

        while self.spawn_timer >= interval and len(self.particles) < self.max_particles:
            self._spawn_particle()
            self.spawn_timer -= interval

    def _spawn_particle(self):
        """Spawn a particle in spawn area or screen edge."""
        preset = self.preset
        direction = self.direction_override or preset.get("direction", (0, -1))
        speed_range = self.speed_override or preset.get("speed_range", (40, 100))

        # Spawn position
        if self.spawn_area:
            # Custom area: (x, y, width, height)
            ax, ay, aw, ah = self.spawn_area
            x = random.randint(int(ax), int(ax + aw))
            y = random.randint(int(ay), int(ay + ah))
        else:
            # Edge spawn based on direction
            if direction[1] < 0:  # Moving up
                x = random.randint(0, self.width)
                y = self.height + 10
            elif direction[1] > 0:  # Moving down
                x = random.randint(0, self.width)
                y = -10
            elif direction[0] < 0:  # Moving left
                x = self.width + 10
                y = random.randint(0, self.height)
            elif direction[0] > 0:  # Moving right
                x = -10
                y = random.randint(0, self.height)
            else:
                x = random.randint(0, self.width)
                y = random.randint(0, self.height)

        # Random properties
        color = random.choice(preset["colors"])
        size = random.randint(*preset["size_range"])
        speed = random.uniform(*speed_range)
        lifetime_range = self.lifetime_override or preset.get("lifetime", (1.0, 3.0))
        lifetime = random.uniform(*lifetime_range)
        spread = preset.get("spread", 0)

        # Direction with spread
        base_angle = math.degrees(math.atan2(direction[1], direction[0]))
        angle = base_angle + random.uniform(-spread / 2, spread / 2)
        rad = math.radians(angle)

        particle = Particle(
            x=x,
            y=y,
            vx=math.cos(rad) * speed,
            vy=math.sin(rad) * speed,
            size=size,
            color=color,
            lifetime=lifetime,
            glow=preset.get("glow", False),
            shrink=preset.get("shrink", False),
            grow=preset.get("grow", False),
            fade_delay=preset.get("fade_delay", 0.0),
        )
        self.particles.append(particle)

    def render(self, draw_manager, layer=Layers.PARTICLES):
        """Render overlay particles."""

        for p in self.particles:
            sprite = SpriteCache.get_sprite(p.color, p.size, p.glow)

            if p.alpha < 255:
                sprite = sprite.copy()
                sprite.set_alpha(p.alpha)

            rect = sprite.get_rect(center=(int(p.x), int(p.y)))
            draw_manager.queue_draw(sprite, rect, layer=layer)

        # Debug: show spawn area when F3 pressed
        if Debug.HITBOX_VISIBLE and self.spawn_area:
            ax, ay, aw, ah = self.spawn_area
            debug_rect = pygame.Rect(ax, ay, aw, ah)
            draw_manager.queue_hitbox(debug_rect, color=(255, 255, 0), width=2)

    def clear(self):
        """Clear all particles."""
        self.particles.clear()

    @property
    def particle_count(self):
        return len(self.particles)
