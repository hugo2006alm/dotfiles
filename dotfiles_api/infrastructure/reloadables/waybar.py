from dotfiles_api.domain.contracts.reloadable import Reloadable
from dotfiles_api.context.execution import ExecutionContext

class WaybarReloadable(Reloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        self._exec.execute(["sh", "-c", "pkill waybar; hyprctl dispatch 'hl.dsp.exec_cmd(\"waybar\")'"])
