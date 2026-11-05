from typing import Protocol
from pathlib import Path
from dotfiles_api.domain.contracts.command_result import CommandResult
from dotfiles_api.domain.contracts.process_handle import ProcessHandle

class CommandExecutor(Protocol):
    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        ...

    def spawn(self, args: list[str], cwd: Path | None = None) -> ProcessHandle:
        ...
