import json
from pathlib import Path
from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.domain.contracts.theme_store import ThemeStore
from dotfiles_api.context.execution import ExecutionContext

class VesktopReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext, theme_store: ThemeStore) -> None:
        self._exec = exec_ctx
        self._theme_store = theme_store

    def reload(self) -> None:
        theme_name = self._theme_store.get_active_theme()
        settings_path = Path.home() / ".config" / "vesktop" / "settings" / "settings.json"
        
        if not settings_path.exists():
            # If Vencord settings file doesn't exist, we don't do anything
            return

        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            # Handle malformed json or other file errors gracefully
            return

        data["enabledThemes"] = [f"{theme_name}.theme.css"]

        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def supports(self, generator_name: str) -> bool:
        return generator_name == "vesktop"
