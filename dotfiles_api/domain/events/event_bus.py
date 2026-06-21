from typing import TypeVar, Type, Callable, Any

T = TypeVar('T')

class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[Type[Any], list[Callable[..., None]]] = {}

    def subscribe(self, event_type: Type[T], handler: Callable[[T], None]) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event: Any) -> None:
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(event)
