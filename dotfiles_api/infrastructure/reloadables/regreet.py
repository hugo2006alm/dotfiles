from dotfiles_api.domain.contracts.reloadable import EventReloadable
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext

class ReGreetReloadable(EventReloadable):
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def reload(self) -> None:
        print("Login theme prepared. Run dotfiles setup-login in a terminal to update greetd.")

    def supports(self, generator_name: str) -> bool:
        return generator_name in ["regreet", "greetd"]
