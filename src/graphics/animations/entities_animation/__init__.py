"""
Entities package - complex entity-specific animations.
Centralized export point for player animation functions.
"""

from .player_animation import (
    death_player,
    damage_player,
)

__all__ = [
    "death_player",
    "damage_player",
]
