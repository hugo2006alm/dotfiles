from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class WalkerReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        self._exec.execute(["systemctl", "--user", "try-restart", "shade-raid-walker.service"],
                           step="reload:walker")

    def supports(self, generator_name: str) -> bool:
        return generator_name == "walker"
