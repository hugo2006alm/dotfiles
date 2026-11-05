from typing import Protocol
from pathlib import Path

class Linker(Protocol):
    def preflight(self, source_dir: Path, target_dir: Path) -> None:
        ...

    def prepare(self, source_dir: Path, target_dir: Path):
        ...

    def link(self, source_dir: Path, target_dir: Path) -> None:
        ...
