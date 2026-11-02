from pathlib import Path
from dataclasses import dataclass

@dataclass(frozen=True)
class EnvironmentContext:
    home_dir: Path
    dotfiles_dir: Path
    user: str
    state_home: Path | None = None
    runtime_home: Path | None = None

    @property
    def source_home(self) -> Path:
        return self.dotfiles_dir / "home"

    @property
    def state_dir(self) -> Path:
        return (self.state_home or self.home_dir / ".local/state") / "shade-raid"

    @property
    def runtime_dir(self) -> Path:
        return self.runtime_home / "shade-raid" if self.runtime_home else self.state_dir / "runtime"

    @property
    def lock_dir(self) -> Path:
        return self.runtime_dir if self.runtime_home else self.home_dir / ".shade-raid-locks"

    def validate_output_path(self, path: Path) -> None:
        resolved = path.resolve()
        if resolved.is_relative_to(self.dotfiles_dir.resolve()):
            raise ValueError(f"Generated output points into the repository: {path}. Run dotfiles link first.")
        if not any(resolved.is_relative_to(base.resolve()) for base in
                   (self.home_dir, self.state_dir, self.runtime_dir)):
            raise ValueError(f"Generated output is outside managed user locations: {path}")
