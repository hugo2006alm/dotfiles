from dotfiles_api.domain.contracts.reloadable import Reloadable
from dotfiles_api.context.execution import ExecutionContext

class WalkerReloadable(Reloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        self._exec.execute(["pkill", "walker"])
        self._exec.execute(["hyprctl", "dispatch", "exec", "walker --gapplication-service"])
