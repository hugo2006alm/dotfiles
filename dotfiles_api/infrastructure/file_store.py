from pathlib import Path
from dotfiles_api.domain.contracts import ThemeStore
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.infrastructure.file_writer import SystemFileWriter

class FileThemeStore(ThemeStore):
    def __init__(self, env: EnvironmentContext) -> None:
        self._env = env
        self._theme_file = self._env.state_dir / "active-theme"

    def get_active_theme(self) -> str:
        if self._theme_file.exists():
            return self._theme_file.read_text().strip()
        legacy = self._env.home_dir / ".config/themes/current"
        if legacy.exists():
            return legacy.read_text().strip()
        return "shade-raid"

    def set_active_theme(self, theme_name: str) -> None:
        self._env.validate_output_path(self._theme_file)
        self._theme_file.parent.mkdir(parents=True, exist_ok=True)
        SystemFileWriter().write(self._theme_file, theme_name + "\n")
