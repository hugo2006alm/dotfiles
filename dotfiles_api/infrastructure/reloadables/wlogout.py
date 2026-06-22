from dotfiles_api.domain.contracts.reloadable import Reloadable
from dotfiles_api.context.execution import ExecutionContext

class WlogoutReloadable(Reloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        res = self._exec.execute(["pgrep", "-x", "wlogout"])
        if res.returncode == 0:
            self._exec.execute(["pkill", "-x", "wlogout"])
            self._exec.execute(["hyprctl", "dispatch", "hl.dsp.exec_cmd('wlogout')"])
