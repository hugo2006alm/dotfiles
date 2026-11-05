from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class WlogoutReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        res = self._exec.query(["pgrep", "-x", "wlogout"])
        if res.returncode == 0:
            self._exec.query(["pkill", "-x", "wlogout"])
            self._exec.execute(["hyprctl", "dispatch", "hl.dsp.exec_cmd('power-menu')"])

    def supports(self, generator_name: str) -> bool:
        return generator_name == "wlogout"

