from dotfiles_api.domain.capabilities.notification_center import NotificationCenter
from dotfiles_api.context.execution import ExecutionContext

class SwayNCNotificationCenter(NotificationCenter):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def toggle_center(self) -> None:
        self._exec.execute(["swaync-client", "-t", "-sw"])
