from pathlib import Path
from dataclasses import dataclass
from dotfiles_api.domain.contracts import CommandExecutor, CommandResult

@dataclass(frozen=True)
class ExecutionContext:
    dry_run: bool
    executor: CommandExecutor

    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        if self.dry_run:
            print(f"[DRY-RUN] Would execute: {' '.join(args)}")
            return CommandResult(stdout="", stderr="", returncode=0)
        return self.executor.execute(args, cwd)
