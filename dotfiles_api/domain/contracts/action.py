from typing import Protocol

class Action(Protocol):
    def execute(self, args: list[str]) -> None:
        ...
