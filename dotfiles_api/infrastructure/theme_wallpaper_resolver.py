from pathlib import Path

from dotfiles_api.context.environment import EnvironmentContext


class ThemeWallpaperResolver:
    def __init__(self, env: EnvironmentContext) -> None:
        self._env = env

    def base_theme_name(self, theme_name: str) -> str:
        if theme_name.endswith("-dark"):
            return theme_name[:-5]
        return theme_name

    def wallpaper_dir(self, theme_name: str) -> Path:
        theme_dir = self._env.home_dir / "wallpapers" / theme_name
        if theme_dir.is_dir():
            return theme_dir
        return self._env.home_dir / "wallpapers" / self.base_theme_name(theme_name)

    def wallpapers(self, theme_name: str) -> list[Path]:
        wp_dir = self.wallpaper_dir(theme_name)
        if not wp_dir.is_dir():
            return []
        return sorted(list(wp_dir.glob("*.jpg")) + list(wp_dir.glob("*.png")))

    def first_wallpaper(self, theme_name: str) -> Path | None:
        wallpapers = self.wallpapers(theme_name)
        if not wallpapers:
            return None
        return wallpapers[0].resolve()
