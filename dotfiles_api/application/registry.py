from typing import Any

class PackageRegistry:
    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        self._mapping = mapping if mapping is not None else {}

    def resolve_source(self, package: str) -> str:
        return self._mapping.get(package, "pacman")
