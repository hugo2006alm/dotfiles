import random
from pathlib import Path
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.infrastructure.theme_wallpaper_resolver import ThemeWallpaperResolver
from dotfiles_api.infrastructure.file_store import FileThemeStore

class WallpaperAction(Action):
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env
        self._wallpapers = ThemeWallpaperResolver(env)

    def execute(self, args: list[str]) -> None:
        theme = FileThemeStore(self._env).get_active_theme()
        
        wp_dir = self._wallpapers.wallpaper_dir(theme)

        if not wp_dir.exists():
            self._exec.optional(["notify-send", "Wallpaper Error", f"Directory {wp_dir} not found"])
            return

        cache_dir = self._env.home_dir / ".cache" / "shade-raid"
        last_wp_file = cache_dir / "last_wallpaper"
        current_wall = ""
        if last_wp_file.exists():
            try:
                current_wall = last_wp_file.read_text().strip()
            except Exception:
                pass

        imgs = [str(path) for path in self._wallpapers.wallpapers(theme)]
        if not imgs:
            self._exec.optional(["notify-send", "Wallpaper Error", "No wallpapers found"])
            return

        candidates = [img for img in imgs if Path(img).resolve() != Path(current_wall).resolve()]
        if not candidates:
            candidates = imgs

        selected_wall = Path(random.choice(candidates)).resolve()

        self._exec.execute([
            "awww", "img", str(selected_wall),
            "--transition-type", "wipe",
            "--transition-angle", "30"
        ])
        self._exec.optional(["notify-send", "Wallpaper Changed", selected_wall.name])
        self._exec.optional(["swaync-client", "-R"])

        if not self._exec.dry_run:
            cache_dir.mkdir(parents=True, exist_ok=True)
            last_wp_file.write_text(str(selected_wall))
