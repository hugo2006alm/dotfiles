from dotfiles_api.domain.contracts.reloadable import Reloadable
from dotfiles_api.domain.contracts.theme_store import ThemeStore
from dotfiles_api.context.execution import ExecutionContext

class GsettingsReloadable(Reloadable):
    def __init__(self, exec_ctx: ExecutionContext, theme_store: ThemeStore) -> None:
        self._exec = exec_ctx
        self._theme_store = theme_store

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
