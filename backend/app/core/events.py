
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class Event:
    name: str
    data: Dict[str, Any]
    source: Optional[str] = None


_EVENT_HANDLERS: Dict[str, List[Callable]] = {}


def on_event(event_name: str):
    def decorator(func: Callable):
        if event_name not in _EVENT_HANDLERS:
            _EVENT_HANDLERS[event_name] = []
        _EVENT_HANDLERS[event_name].append(func)
        logger.debug(f"[EventRegister] {event_name} -> {func.__name__}")
        return func
    return decorator


def emit_event(event_name: str, data: Dict[str, Any], source: Optional[str] = None) -> None:
    event = Event(name=event_name, data=data, source=source)
    handlers = _EVENT_HANDLERS.get(event_name, [])

    if not handlers:
        logger.debug(f"[EventPublish] {event_name} - no handlers")
        return

    logger.info(f"[EventPublish] {event_name} - {len(handlers)} handlers")

    for handler in handlers:
        try:
            handler(event)
        except Exception as e:
            logger.error(f"[EventHandlerFailed] {event_name} - {handler.__name__}: {e}")


def get_event_handlers(event_name: str) -> List[Callable]:
    return _EVENT_HANDLERS.get(event_name, []).copy()


def get_all_events() -> List[str]:
    return list(_EVENT_HANDLERS.keys())


def discover_event_handlers():
    total_handlers = sum(len(handlers) for handlers in _EVENT_HANDLERS.values())
    logger.debug(f"[EventDiscovery] Loaded {len(_EVENT_HANDLERS)} events, {total_handlers} handlers")


def clear_handlers(event_name: Optional[str] = None) -> None:
    if event_name is None:
        _EVENT_HANDLERS.clear()
        logger.debug("[EventSystem] Clear all handlers")
    else:
        _EVENT_HANDLERS.pop(event_name, None)
        logger.debug(f"[EventSystem] Clear handlers for {event_name}")
