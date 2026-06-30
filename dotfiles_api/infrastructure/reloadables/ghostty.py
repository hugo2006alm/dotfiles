from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class GhosttyReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        self._exec.execute(["pkill", "-USR2", "ghostty"])

    def supports(self, generator_name: str) -> bool:
        return generator_name == "ghostty"
