from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.execution import ExecutionContext

class CommandAction(Action):
    def __init__(self, exec_ctx: ExecutionContext, commands: list[list[str]]) -> None:
        self._exec = exec_ctx
        self._commands = commands

    def execute(self, args: list[str]) -> None:
        for cmd in self._commands:
            self._exec.execute(cmd + args)
