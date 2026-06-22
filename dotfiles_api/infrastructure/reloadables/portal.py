from pathlib import Path
from dotfiles_api.domain.contracts.reloadable import Reloadable
from dotfiles_api.context.execution import ExecutionContext

class XDGPortalReloadable(Reloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        self._exec.execute(["bash", "-c", "killall -9 xdg-desktop-portal-hyprland xdg-desktop-portal 2>/dev/null; /usr/lib/xdg-desktop-portal-hyprland >/dev/null 2>&1 & sleep 2; /usr/lib/xdg-desktop-portal >/dev/null 2>&1 &"])
