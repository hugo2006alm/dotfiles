from pathlib import Path
from dataclasses import dataclass
from dotfiles_api.domain.contracts import CommandExecutor, CommandResult

@dataclass(frozen=True)
class ExecutionContext:
    dry_run: bool
    executor: CommandExecutor
    verbose: bool = False

    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        if self.dry_run:
            print(f"[DRY-RUN] Would execute: {' '.join(args)}")
            return CommandResult(stdout="", stderr="", returncode=0)
        if self.verbose:
            print(f"[VERBOSE] Executing command: {' '.join(args)}")
        res = self.executor.execute(args, cwd)
        if self.verbose and res.returncode != 0:
            print(f"[VERBOSE] Command failed with code {res.returncode}. stderr: {res.stderr}")
        return res
