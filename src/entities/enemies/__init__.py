"""
Enemy entity package.
Imports all enemy types to trigger auto-registration.
"""

from .enemy_straight import EnemyStraight
from .enemy_homing import EnemyHoming
from .waypoint_shooter import WaypointShooter
from .enemy_waypoint import EnemyWaypoint

__all__ = [
    'EnemyStraight',
    'EnemyHoming',
    'WaypointShooter',
    'EnemyWaypoint',
]