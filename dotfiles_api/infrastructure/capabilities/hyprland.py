from dotfiles_api.domain.capabilities.compositor import Compositor
from dotfiles_api.context.execution import ExecutionContext

class HyprlandCompositor(Compositor):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload_compositor(self) -> None:
        self._exec.execute(["hyprctl", "reload"])
