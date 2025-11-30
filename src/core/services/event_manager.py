"""
event_manager.py
----------------
Event-driven system for decoupled game component communication.
Enables items, enemies, and player to communicate without direct dependencies.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Type
from src.core.debug.debug_logger import DebugLogger


# ===========================================================
# Event Definitions
# ===========================================================

@dataclass(frozen=True)
class BaseEvent:
    """Base class for all events."""
    pass


@dataclass(frozen=True)
class EnemyDiedEvent(BaseEvent):
    """Dispatched when an enemy dies."""
    position: tuple
    enemy_type_tag: str
    exp: int


@dataclass(frozen=True)
class ItemCollectedEvent(BaseEvent):
    """Dispatched when player collects an item."""
    effects: list


@dataclass(frozen=True)
class PlayerHealthEvent(BaseEvent):
    """Dispatched to modify player health."""
    amount: int


@dataclass(frozen=True)
class FireRateEvent(BaseEvent):
    """Dispatched to modify player fire rate."""
    multiplier: float
    duration: float


@dataclass(frozen=True)
class NukeUsedEvent(BaseEvent):
    """Dispatched when a bomb is used to clear the screen."""
    damage: int = 9999


@dataclass(frozen=True)
class ScreenShakeEvent(BaseEvent):
    """Dispatched to trigger screen shake effect."""
    intensity: float = 8.0
    duration: float = 0.3


@dataclass(frozen=True)
class BulletClearEvent(BaseEvent):
    """Dispatched to clear enemy bullets in an area."""
    center: tuple
    radius: float
    owner: str = "enemy"  # Which bullets to clear


@dataclass(frozen=True)
class SpawnPauseEvent(BaseEvent):
    """Dispatched to pause/resume enemy spawning."""
    paused: bool


# ===========================================================
# Event Manager
# ===========================================================
class EventManager:
    """Central event dispatcher using pub-sub pattern."""

    def __init__(self):
        self._subscribers: Dict[Type[BaseEvent], List[Callable]] = {}
        DebugLogger.init("EventManager initialized")

    # ===========================================================
    # Subscription
    # ===========================================================

    def subscribe(self, event_type: Type[BaseEvent], callback: Callable) -> None:
        """
        Register a callback for an event type.

        Args:
            event_type: Event class to listen for
            callback: Function to call when event fires
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if callback in self._subscribers[event_type]:
            return

        self._subscribers[event_type].append(callback)
        callback_name = getattr(callback, '__name__', repr(callback))
        DebugLogger.system(
            f"Subscribed '{callback_name}' to '{event_type.__name__}'",
            category="event_manager"
        )

    def unsubscribe(self, event_type: Type[BaseEvent], callback: Callable) -> None:
        """
        Remove a callback from an event type.

        Args:
            event_type: Event class
            callback: Function to remove
        """
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    def unsubscribe_all(self, callback: Callable) -> None:
        """
        Remove a callback from all event types.

        Args:
            callback: Function to remove everywhere
        """
        for subscribers in self._subscribers.values():
            try:
                subscribers.remove(callback)
            except ValueError:
                pass

    # ===========================================================
    # Dispatch
    # ===========================================================

    def dispatch(self, event: BaseEvent) -> None:
        """
        Send event to all registered callbacks.

        Args:
            event: Event instance to dispatch
        """
        event_type = type(event)

        if event_type not in self._subscribers:
            return

        for callback in list(self._subscribers[event_type]):
            try:
                callback(event)
            except Exception as e:
                callback_name = getattr(callback, '__name__', repr(callback))
                DebugLogger.warn(f"Error in event callback {callback_name}: {e}")

    # ===========================================================
    # Lifecycle
    # ===========================================================

    def clear_event_type(self, event_type: Type[BaseEvent]) -> None:
        """
        Remove all subscribers for a specific event type.

        Args:
            event_type: Event class to clear
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].clear()

    def clear_all(self) -> None:
        """Remove all subscribers. Call on scene exit."""
        self._subscribers.clear()

    def get_subscriber_count(self, event_type: Type[BaseEvent] = None) -> int:
        """
        Get count of subscribers.

        Args:
            event_type: Specific event type, or None for total

        Returns:
            Number of subscribers
        """
        if event_type:
            return len(self._subscribers.get(event_type, []))
        return sum(len(subs) for subs in self._subscribers.values())


# ===========================================================
# Singleton Access
# ===========================================================

_EVENTS = None


def get_events() -> EventManager:
    """Get or create the event manager singleton."""
    global _EVENTS
    if _EVENTS is None:
        _EVENTS = EventManager()
    return _EVENTS


def reset_events() -> None:
    """Reset the singleton. Call on full game restart."""
    global _EVENTS
    _EVENTS = None