from typing import Protocol

class PackageSource(Protocol):
    def is_available(self) -> bool:
        ...
    def install(self, packages: list[str]) -> None:
        ...
