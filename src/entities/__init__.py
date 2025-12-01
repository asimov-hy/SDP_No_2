"""
src/entities/__init__.py
------------------------
Entity module exports.

Provides core entity states and type constants used across all game entities.
These are lightweight enums and constants with no heavy dependencies.

Exports:
    LifecycleState  - Entity life/death progression (ALIVE, DYING, DEAD)
    InteractionState - Collision interaction modes (DEFAULT, INVINCIBLE, etc.)
    EntityCategory   - Logical entity groupings (PLAYER, ENEMY, PROJECTILE, etc.)
    CollisionTags    - Collision tag constants (PLAYER, ENEMY_BULLET, etc.)
"""

from src.entities.entity_state import LifecycleState, InteractionState
from src.entities.entity_types import EntityCategory, CollisionTags

__all__ = [
    # States
    'LifecycleState',
    'InteractionState',
    # Types
    'EntityCategory',
    'CollisionTags',
]