from typing import Protocol

class Reloadable(Protocol):
    def reload(self) -> None:
        ...
