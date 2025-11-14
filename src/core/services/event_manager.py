"""
event_manager.py
----------------
Provides a central, singleton EventManager for handling event subscriptions
and dispatching. This allows for loose coupling between different game systems.
"""
from dataclasses import dataclass
from collections import defaultdict
from typing import Callable, Any, Type, Dict, Set, List
from functools import partial # Added import
from src.core.debug.debug_logger import DebugLogger

# ===========================================================
# Global Event Definitions
# ===========================================================
@dataclass(frozen=True)
class BaseEvent:
    pass

@dataclass(frozen=True)
class EntityDiedEvent(BaseEvent):
    position: tuple[float, float]

@dataclass(frozen=True)
class EnemyDiedEvent(EntityDiedEvent):
    enemy_type_tag: str

@dataclass(frozen=True)
class ItemCollectedEvent(BaseEvent):
    effects: list

@dataclass(frozen=True)
class PlayerHealthEvent(BaseEvent):
    amount: int

@dataclass(frozen=True)
class FireRateEvent(BaseEvent):
    multiplier: float
    duration: float

SubscriberCallback = Callable[[Any], None]
class EventManager:
    """
    A central event manager for handling event subscriptions and dispatching.
    Implemented as a singleton to ensure a single event bus for the application.
    """
    _instance = None

    def __init__(self) -> None:
        self._subscribers: Dict[Type[BaseEvent], Set[SubscriberCallback]] = defaultdict(set)

    def subscribe(self, event_type: Type[BaseEvent], callback: SubscriberCallback) -> None:
        """
        Registers a callback for a specific event type.

        Args:
            event_type (Type[BaseEvent]): The event to subscribe to (e.g., EntityDiedEvent).
            callback (SubscriberCallback): The function to call when the event occurs.
        """
        self._subscribers[event_type].add(callback)
        callback_name = callback.func.__name__ if isinstance(callback, partial) else callback.__name__
        DebugLogger.system(f"Subscribed '{callback_name}' to event '{event_type.__name__}'", category="event")

    def unsubscribe(self, event_type: Type[BaseEvent], callback: SubscriberCallback) -> None:
        """
        Unregisters a callback from a specific event type.

        Args:
            event_type (Type[BaseEvent]): The event to unsubscribe from.
            callback (Callable): The callback function to remove.
        """
        self._subscribers[event_type].discard(callback)
        callback_name = callback.func.__name__ if isinstance(callback, partial) else callback.__name__
        DebugLogger.system(f"Unsubscribed '{callback_name}' from event '{event_type.__name__}'", category="event")

    def dispatch(self, event: BaseEvent) -> None:
        """
        Dispatches an event, calling all registered callbacks for that type.

        Args:
            event (BaseEvent): The event to dispatch.
        """
        event_type: Type[BaseEvent] = type(event)
        subscribers_to_notify: List[SubscriberCallback] = list(self._subscribers.get(event_type, set()))
        DebugLogger.system(f"Dispatching event '{event_type.__name__}' to {len(subscribers_to_notify)} subscribers", category="event")
        # Iterate over a copy to allow unsubscription during dispatch
        for subscriber in subscribers_to_notify:
            try:
                subscriber(event)
            except Exception as e:
                DebugLogger.fail(f"Error in event handler for '{event}': {e}", category="event")

# ===========================================================
# Global Instance
# ===========================================================
# Global singleton instance for easy access throughout the game
EVENTS = EventManager()

