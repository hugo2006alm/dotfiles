from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class GhosttyReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        # Ghostty automatically hot-reloads when colors.conf is modified on disk.
        # Sending USR2 signal is redundant and causes it to reload twice.
        pass

    def supports(self, generator_name: str) -> bool:
        return generator_name == "ghostty"
