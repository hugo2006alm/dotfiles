from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class SwayNCReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        self._exec.execute(["swaync-client", "-R"], step="reload:swaync-config")
        self._exec.execute(["swaync-client", "-rs"], step="reload:swaync-css")

    def supports(self, generator_name: str) -> bool:
        return generator_name == "swaync"
