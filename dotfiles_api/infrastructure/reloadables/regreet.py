from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext

class ReGreetReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def reload(self) -> None:
        src = self._env.home_dir / ".config" / "greetd" / "regreet.css"
        dst = "/etc/greetd/regreet.css"
        self._exec.execute(["sudo", "/usr/bin/cp", str(src), dst])

    def supports(self, generator_name: str) -> bool:
        return generator_name in ["regreet", "greetd"]
