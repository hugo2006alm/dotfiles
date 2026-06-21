from typing import Protocol
from pathlib import Path

class Linker(Protocol):
    def link(self, source_dir: Path, target_dir: Path) -> None:
        ...
