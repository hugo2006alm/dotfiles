from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.domain.contracts.theme_store import ThemeStore
from dotfiles_api.context.execution import ExecutionContext
import shutil
from dotfiles_api.application.loader import ThemeLoader

class GsettingsReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext, theme_store: ThemeStore, loader: ThemeLoader | None = None) -> None:
        self._exec = exec_ctx
        self._theme_store = theme_store
        self._loader = loader

    def reload(self) -> None:
        theme = self._theme_store.get_active_theme()
        if "dark" in theme:
            scheme = "prefer-dark"
            gtk_theme = "Adwaita-dark"
            icon_theme = "Papirus-Dark"
        else:
            scheme = "prefer-light"
            gtk_theme = "Adwaita"
            icon_theme = "Papirus-Light"

        self._exec.execute(["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", scheme])
        self._exec.execute(["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", gtk_theme])
        self._exec.execute(["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", icon_theme])
        if self._loader is not None and shutil.which("papirus-folders"):
            colors = self._loader.load(theme).colors.colors
            folder = colors.get("papirus_folder_color")
            if not folder:
                accent = colors.get("accent", "")
                folder = "orange" if accent in {"#D94F2B", "#E8623E", "#B33E20"} else \
                         "green" if accent in {"#6B8E23", "#556B2F"} else "grey"
            self._exec.optional(["papirus-folders", "-C", folder], step="reload:gtk-folders")

    def supports(self, generator_name: str) -> bool:
        return generator_name == "gtk"
