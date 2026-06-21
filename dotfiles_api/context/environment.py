from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class EnvironmentContext:
    home_dir: Path
    dotfiles_dir: Path
    user: str
