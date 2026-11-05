from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class WaybarReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def reload(self) -> None:
        signal_result = self._exec.query(["pkill", "-USR2", "waybar"])
        running_result = self._exec.query(["pgrep", "-x", "waybar"])
        if signal_result.returncode != 0 or running_result.returncode != 0:
            self._exec.execute(["hyprctl", "dispatch", "hl.dsp.exec_cmd('waybar')"])

    def supports(self, generator_name: str) -> bool:
        return generator_name == "waybar"
