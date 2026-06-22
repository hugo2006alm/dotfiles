from pathlib import Path
from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext

class WaybarReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def compile_styles(self) -> None:
        home_dir = Path.home()
        style_scss = home_dir / ".config" / "waybar" / "style.scss"
        style_css = home_dir / ".config" / "waybar" / "style.css"
        self._exec.execute(["sassc", str(style_scss), str(style_css)])

    def reload(self) -> None:
        self.compile_styles()
        self._exec.execute(["pkill", "-USR2", "waybar"])

    def supports(self, generator_name: str) -> bool:
        return generator_name == "waybar"
