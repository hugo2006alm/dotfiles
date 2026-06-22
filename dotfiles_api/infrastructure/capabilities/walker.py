from dotfiles_api.domain.capabilities.launcher import Launcher
from dotfiles_api.context.execution import ExecutionContext

class WalkerLauncher(Launcher):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def launch(self) -> None:
        self._exec.execute(["walker"])
