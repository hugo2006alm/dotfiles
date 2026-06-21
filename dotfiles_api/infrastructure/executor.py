import subprocess
from pathlib import Path
from dotfiles_api.domain.contracts import CommandResult, CommandExecutor

class SystemCommandExecutor(CommandExecutor):
    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        try:
            res = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                text=True
            )
            return CommandResult(
                stdout=res.stdout,
                stderr=res.stderr,
                returncode=res.returncode
            )
        except FileNotFoundError as e:
            return CommandResult(
                stdout="",
                stderr=str(e),
                returncode=127
            )
