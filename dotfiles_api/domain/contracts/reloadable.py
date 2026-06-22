from typing import Protocol, runtime_checkable

@runtime_checkable
class Reloadable(Protocol):
    def reload(self) -> None:
        ...

@runtime_checkable
class EventReloadable(Reloadable, Protocol):
    def supports(self, generator_name: str) -> bool:
        ...
