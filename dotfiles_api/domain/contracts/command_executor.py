from typing import Protocol
from pathlib import Path
from dotfiles_api.domain.contracts.command_result import CommandResult

class CommandExecutor(Protocol):
    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        ...
