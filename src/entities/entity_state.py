"""
entity_state.py
---------------
Defines universal constants and enumerations for all entity types.

Responsibilities
----------------
- Provide standardized interaction and collision states shared across all entities.
- Define global entity constants (tags, defaults).
- Remain free of gameplay-specific or player-only logic.
"""

from enum import IntEnum

# ===========================================================
# Shared Entity Constants
# ===========================================================
DEFAULT_ENTITY_TAG = "entity"  # Generic fallback collision tag
DEFAULT_HEALTH = 1             # Default HP for destructible entities


# ===========================================================
# Entity Interaction States
# ===========================================================
class InteractionState(IntEnum):
    """
    Defines the basic collision and interaction behavior for all entities.

    This state determines how an entity interacts with collision systems,
    damage, and other entities. Used by players, enemies, and bullets.

    State Levels (ascending immunity):
    -----------------------------------
    DEFAULT (0):
        Normal behavior — entity can take damage and collides normally.
        Hitbox is fully active and participates in all collision checks.

    INVINCIBLE (1):
        Cannot take damage but still has physical collision.
        Useful for: post-hit invulnerability frames, power-ups, cutscenes.
        Hitbox is active but damage is ignored.

    INTANGIBLE (2):
        Passes through certain entities or projectiles.
        Useful for: dash abilities, teleportation, phase-through mechanics.
        Hitbox may be selectively inactive based on collision tags.

    CLIP_THROUGH (3):
        No collision or interaction whatsoever (debug/ghost mode).
        Useful for: debugging, cinematic cameras, removed but animating entities.
        Hitbox is completely inactive.
    """
    DEFAULT = 0
    INVINCIBLE = 1
    INTANGIBLE = 2
    CLIP_THROUGH = 3

    @property
    def can_take_damage(self) -> bool:
        """Check if entity can receive damage in this state."""
        return self == InteractionState.DEFAULT

    @property
    def has_collision(self) -> bool:
        """Check if entity has physical collision in this state."""
        return self <= InteractionState.INVINCIBLE

    @property
    def is_tangible(self) -> bool:
        """Check if entity is solid/tangible in this state."""
        return self <= InteractionState.INTANGIBLE


# ===========================================================
# Collision Tag Constants
# ===========================================================
class CollisionTags:
    """
    Standard collision tags used throughout the entity system.

    Using constants instead of magic strings prevents typos and
    makes refactoring easier. These should be used as values for
    entity.collision_tag.

    Collision rules are defined in CollisionManager.rules, not here.
    This class only provides the tag constants themselves.
    """
    # Neutral / Default
    NEUTRAL = "neutral"
    ENTITY = "entity"

    # Player
    PLAYER = "player"
    PLAYER_BULLET = "player_bullet"

    # Enemies
    ENEMY = "enemy"
    ENEMY_BULLET = "enemy_bullet"

    # Environment
    WALL = "wall"
    PICKUP = "pickup"
    HAZARD = "hazard"

    # Special
    INVULNERABLE = "invulnerable"  # For decorative entities that never collide


# ===========================================================
# Health Constants
# ===========================================================
class HealthPresets:
    """
    Standard health values for different entity types.

    Provides consistent baseline values across the game.
    Individual entities can override these in their constructors.
    """
    # Bullets (instant destroy on hit)
    BULLET = 1

    # Basic enemies
    ENEMY_WEAK = 1
    ENEMY_NORMAL = 3
    ENEMY_STRONG = 5
    ENEMY_ELITE = 10

    # Mini-bosses and bosses
    MINI_BOSS = 50
    BOSS = 100

    # Player (often uses different damage system)
    PLAYER_DEFAULT = 3