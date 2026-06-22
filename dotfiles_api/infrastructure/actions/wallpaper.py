import os
import glob
import random
import shutil
from pathlib import Path
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext

class WallpaperAction(Action):
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def execute(self, args: list[str]) -> None:
        theme_file = self._env.home_dir / ".config" / "themes" / "current"
        theme = "shade-raid"
        if theme_file.exists():
            try:
                theme = theme_file.read_text().strip()
            except Exception:
                pass
        
        base_theme = theme.split("-")[0]

        wp_dir = self._env.home_dir / "wallpapers" / theme
        if not wp_dir.exists():
            wp_dir = self._env.home_dir / "wallpapers" / base_theme

        if not wp_dir.exists():
            self._exec.execute(["notify-send", "Wallpaper Error", f"Directory {wp_dir} not found"])
            return

        cache_dir = self._env.home_dir / ".cache" / "shade-raid"
        last_wp_file = cache_dir / "last_wallpaper"
        current_wall = ""
        if last_wp_file.exists():
            try:
                current_wall = last_wp_file.read_text().strip()
            except Exception:
                pass

        imgs = glob.glob(str(wp_dir / "*.jpg")) + glob.glob(str(wp_dir / "*.png"))
        if not imgs:
            self._exec.execute(["notify-send", "Wallpaper Error", "No wallpapers found"])
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
        self._exec.execute(["notify-send", "Wallpaper Changed", selected_wall.name])

        if not self._exec.dry_run:
            cache_dir.mkdir(parents=True, exist_ok=True)
            last_wp_file.write_text(str(selected_wall))

        target_bg = Path("/etc/greetd/regreet-background.jpg")
        target_dir = target_bg.parent
        is_writable = False
        try:
            if target_bg.exists() and os.access(target_bg, os.W_OK):
                is_writable = True
            elif not target_bg.exists() and target_dir.exists() and os.access(target_dir, os.W_OK):
                is_writable = True
        except Exception:
            pass

        if is_writable:
            if shutil.which("convert"):
                self._exec.execute([
                    "convert", str(selected_wall),
                    "-filter", "Gaussian",
                    "-blur", "0x20",
                    "-modulate", "70",
                    str(target_bg)
                ])
            else:
                if self._exec.dry_run:
                    print(f"[DRY-RUN] Would copy {selected_wall} to {target_bg}")
                else:
                    try:
                        shutil.copy(str(selected_wall), str(target_bg))
                    except Exception:
                        pass
