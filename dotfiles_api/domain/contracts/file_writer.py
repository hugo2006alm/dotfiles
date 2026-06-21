from typing import Protocol
from pathlib import Path

class FileWriter(Protocol):
    def write(self, target_path: Path, content: str) -> None:
        ...
