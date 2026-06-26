from pathlib import Path
from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class WlogoutReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def compile_styles(self) -> None:
        home_dir = Path.home()
        style_scss = home_dir / ".config" / "wlogout" / "style.scss"
        style_css = home_dir / ".config" / "wlogout" / "style.css"
        self._exec.execute(["sassc", str(style_scss), str(style_css)])

    def reload(self) -> None:
        self.compile_styles()
        res = self._exec.execute(["pgrep", "-x", "wlogout"])
        if res.returncode == 0:
            self._exec.execute(["pkill", "-x", "wlogout"])
            self._exec.execute(["hyprctl", "dispatch", "hl.dsp.exec_cmd('power-menu')"])

    def supports(self, generator_name: str) -> bool:
        return generator_name == "wlogout"

