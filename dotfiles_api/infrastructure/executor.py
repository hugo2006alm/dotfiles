import subprocess
import sys
from pathlib import Path
from dotfiles_api.domain.contracts import CommandResult, CommandExecutor

class SystemCommandExecutor(CommandExecutor):
    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        privileged = Path(args[0]).name in {"sudo", "yay", "su"}
        if privileged and not sys.stdin.isatty():
            return CommandResult("", "Privileged commands require an interactive terminal; run this command yourself.", 126)
        try:
            interactive = privileged or args[:3] == ["gh", "auth", "login"] or args[0] == "chsh"
            res = subprocess.run(
                args,
                cwd=cwd,
                capture_output=not interactive,
                text=True
            )
            return CommandResult(
                stdout=res.stdout or "",
                stderr=res.stderr or "",
                returncode=res.returncode
            )
        except OSError as e:
            return CommandResult(
                stdout="",
                stderr=str(e),
                returncode=127
            )
