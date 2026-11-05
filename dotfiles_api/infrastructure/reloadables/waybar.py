from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class WaybarReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        self._exec.execute(["systemctl", "--user", "try-reload-or-restart", "shade-raid-waybar.service"],
                           step="reload:waybar")

    def supports(self, generator_name: str) -> bool:
        return generator_name == "waybar"
