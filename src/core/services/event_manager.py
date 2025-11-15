"""
Event-driven system for decoupled game component communication.
Enables items, enemies, and player to communicate without direct dependencies.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Type
from src.core.debug.debug_logger import DebugLogger


# ============================================================
# Event Definitions
# ============================================================

@dataclass(frozen=True)
class BaseEvent:
    """Base class for all events."""
    pass


@dataclass(frozen=True)
class EnemyDiedEvent(BaseEvent):
    """Dispatched when an enemy dies."""
    position: tuple  # (x, y)
    enemy_type_tag: str  # Class name for filtering


@dataclass(frozen=True)
class ItemCollectedEvent(BaseEvent):
    """Dispatched when player collects an item."""
    effects: list  # List of effect dicts from item data


@dataclass(frozen=True)
class PlayerHealthEvent(BaseEvent):
    """Dispatched to modify player health."""
    amount: int  # Positive = heal, negative = damage


@dataclass(frozen=True)
class FireRateEvent(BaseEvent):
    """Dispatched to modify player fire rate."""
    multiplier: float  # e.g., 2.0 = double fire rate
    duration: float  # Seconds (0 = permanent)


# ============================================================
# Event Manager
# ============================================================

class EventManager:
    """Central event dispatcher using pub-sub pattern."""

    def __init__(self):
        self._subscribers: Dict[Type[BaseEvent], List[Callable]] = {}
        DebugLogger.init("EventManager initialized")

    def subscribe(self, event_type: Type[BaseEvent], callback: Callable) -> None:
        """Register a callback for an event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        self._subscribers[event_type].append(callback)
        callback_name = getattr(callback, '__name__', repr(callback))
        DebugLogger.init_sub(
            f"Subscribed '{callback_name}' to '{event_type.__name__}'"
        )

    def unsubscribe(self, event_type: Type[BaseEvent], callback: Callable) -> None:
        """Remove a callback from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    def dispatch(self, event: BaseEvent) -> None:
        """Send event to all registered callbacks."""
        event_type = type(event)

        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    callback_name = getattr(callback, '__name__', repr(callback))
                    DebugLogger.warn(
                        f"Error in event callback {callback_name}: {e}"
                    )


# ============================================================
# Global Instance
# ============================================================

EVENTS = EventManager()