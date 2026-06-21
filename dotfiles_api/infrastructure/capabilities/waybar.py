from dotfiles_api.domain.capabilities.status_bar import StatusBar
from dotfiles_api.context.execution import ExecutionContext

class WaybarStatusBar(StatusBar):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def get_capability_id(self) -> str:
        return "status-bar"

    def toggle(self) -> None:
        self._exec.execute(["pkill", "-USR1", "waybar"])
