"""
entity_state.py
---------------
Defines runtime state enumerations for all entity types.
Contains only states that change over time during gameplay.
"""

from enum import IntEnum


class LifecycleState(IntEnum):
    """
    Tracks the life/death progression of an entity.
    Used for death animation control and cleanup timing.
    """
    ALIVE = 0
    DYING = 1      # Playing death animation/effects
    DEAD = 2       # Ready for cleanup


class InteractionState(IntEnum):
    """
    Defines how the entity collider interacts with others.

    Determines how collisions affect the entity and its surroundings.

    Collision Meaning:
      self        → entity receives damage
      opponent    → collision opponent interacts with entity
      hazard      → entity takes damage from environmental hazards
      environment → interacts physically with walls or terrain

    State Levels:
      0 -> DEFAULT       self: O   opponent: O   hazard: O   environment: O
      1 -> INVINCIBLE    self: X   opponent: O   hazard: O   environment: O
      2 -> INTANGIBLE    self: X   opponent: X   hazard: X   environment: O
      3 -> CLIP_THROUGH  self: X   opponent: X   hazard: X   environment: X
    """
    DEFAULT = 0
    INVINCIBLE = 1
    INTANGIBLE = 2
    CLIP_THROUGH = 3