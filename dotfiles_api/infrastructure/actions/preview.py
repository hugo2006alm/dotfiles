from pathlib import Path
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext

class PreviewAction(Action):
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def execute(self, args: list[str]) -> None:
        if not args:
            return
        direction = args[0]  # "next" or "prev"
        
        # 1. Scan installed themes
        themes_dir = self._env.home_dir / ".config" / "themes"
        if not themes_dir.is_dir():
            return
            
        themes = []
        for item in themes_dir.iterdir():
            if item.is_dir() and (item / "colors.toml").is_file():
                themes.append(item.name)
        
        if not themes:
            return
        themes.sort()
        
        # 2. Get current preview theme
        preview_theme_path = Path("/tmp/dotfiles_preview_theme")
        current_preview = None
        if preview_theme_path.is_file():
            try:
                current_preview = preview_theme_path.read_text().strip()
            except Exception:
                pass
                
        # Fallback to active theme if preview theme is invalid or not in list
        if not current_preview or current_preview not in themes:
            active_theme_path = themes_dir / "current"
            if active_theme_path.is_file():
                try:
                    current_preview = active_theme_path.read_text().strip()
                except Exception:
                    pass
            if not current_preview or current_preview not in themes:
                current_preview = themes[0]
                
        # 3. Increment / decrement with wrapping
        try:
            curr_idx = themes.index(current_preview)
        except ValueError:
            curr_idx = 0
            
        if direction == "next":
            next_idx = (curr_idx + 1) % len(themes)
        elif direction == "prev":
            next_idx = (curr_idx - 1) % len(themes)
        else:
            return
            
        next_theme = themes[next_idx]
        
        # 4. Write back preview theme
        try:
            preview_theme_path.write_text(next_theme)
        except Exception:
            pass
            
        # 5. Regenerate swaync config/style with the new preview theme
        try:
            from dotfiles_api.infrastructure.generators.swaync import SwayncGenerator
            from dotfiles_api.infrastructure.theme.store import FileSystemThemeStore
            from dotfiles_api.infrastructure.theme.loader import ThemeLoader
            
            store = FileSystemThemeStore(self._env)
            active_theme = store.get_active_theme()
            loader = ThemeLoader(self._env)
            tokens = loader.load(active_theme)
            
            gen = SwayncGenerator()
            artifacts = gen.render(tokens, active_theme)
            
            dest_dir = self._env.home_dir / ".config" / "swaync"
            if not self._exec.dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)
                
            for art in artifacts:
                if art.artifact_id == "swaync-config":
                    dest_file = dest_dir / "config.json"
                elif art.artifact_id == "swaync-style":
                    dest_file = dest_dir / "style.css"
                else:
                    continue
                if not self._exec.dry_run:
                    dest_file.write_text(art.content, encoding="utf-8")
        except Exception:
            pass
            
        # 6. Reload swaync config & style in-place
        self._exec.execute(["swaync-client", "-R"])
        self._exec.execute(["swaync-client", "-rs"])
