from pathlib import Path
from dotfiles_api.domain.contracts import ThemeStore
from dotfiles_api.context.environment import EnvironmentContext

class FileThemeStore(ThemeStore):
    def __init__(self, env: EnvironmentContext) -> None:
        self._env = env
        self._theme_file = self._env.home_dir / ".config" / "themes" / "current"

    def get_active_theme(self) -> str:
        if self._theme_file.exists():
            return self._theme_file.read_text().strip()
        return "shade-raid"

    def set_active_theme(self, theme_name: str) -> None:
        self._theme_file.parent.mkdir(parents=True, exist_ok=True)
        self._theme_file.write_text(theme_name)
