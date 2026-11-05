import subprocess
import sys
from pathlib import Path
from dotfiles_api.domain.contracts import CommandResult, CommandExecutor

class SystemCommandExecutor(CommandExecutor):
    @staticmethod
    def _interactive(args: list[str]) -> bool:
        return (Path(args[0]).name in {"sudo", "yay", "su", "chsh"}
                or [Path(args[0]).name, *args[1:3]] == ["gh", "auth", "login"])

    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        privileged = Path(args[0]).name in {"sudo", "yay", "su"}
        if privileged and not sys.stdin.isatty():
            return CommandResult("", "Privileged commands require an interactive terminal; run this command yourself.", 126)
        try:
            interactive = self._interactive(args)
            res = subprocess.run(
                args,
                cwd=cwd,
                capture_output=not interactive,
                text=True
            )
            return CommandResult(
                stdout=res.stdout or "",
                stderr=res.stderr or "",
                returncode=res.returncode,
                output_captured=not interactive,
            )
        except OSError as e:
            return CommandResult(
                stdout="",
                stderr=str(e),
                returncode=127
            )

    def spawn(self, args: list[str], cwd: Path | None = None) -> subprocess.Popen:
        if self._interactive(args):
            raise RuntimeError("Interactive commands cannot be launched in the background")
        # Avoid inherited terminals and full pipes after the CLI exits.
        return subprocess.Popen(args, cwd=cwd, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
