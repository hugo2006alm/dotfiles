from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import sys
from collections.abc import Callable
from dotfiles_api.domain.contracts import CommandExecutor, CommandResult
from dotfiles_api.context.command_error import CommandExecutionError
from dotfiles_api.context.command_logging import redacted_diagnostics

@dataclass(frozen=True)
class ExecutionContext:
    dry_run: bool
    executor: CommandExecutor
    verbose: bool = False
    log_path: Path | None = None
    output_guard: Callable[[Path], None] | None = None

    def execute(self, args: list[str], cwd: Path | None = None, *,
                step: str = "command", allowed_returncodes: tuple[int, ...] = (0,),
                required: bool = True) -> CommandResult:
        command, _ = redacted_diagnostics(args)
        if self.dry_run:
            print(f"[DRY-RUN] Would execute: {command}")
            return CommandResult(stdout="", stderr="", returncode=0)
        if self.log_path is not None and self.output_guard is not None:
            self.output_guard(self.log_path)
        if self.verbose:
            print(f"[VERBOSE] Executing command: {command}")
        res = self.executor.execute(args, cwd)
        _, diagnostic = redacted_diagnostics(args, res.stderr or "")
        failed = res.returncode not in allowed_returncodes
        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            record = {"time": datetime.now(timezone.utc).isoformat(), "command": command,
                      "step": step, "returncode": res.returncode,
                      "required": required, "diagnostic": diagnostic if failed else ""}
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(self.log_path, flags, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(json.dumps(record) + "\n")
        if failed:
            error = CommandExecutionError(command, res.returncode, diagnostic or "see command output", step)
            if required:
                raise error
            print(f"[OPTIONAL] {error}", file=sys.stderr)
        return res

    def optional(self, args: list[str], cwd: Path | None = None, *, step: str = "optional") -> CommandResult:
        return self.execute(args, cwd, step=step, required=False)

    def query(self, args: list[str], cwd: Path | None = None, *,
              allowed_returncodes: tuple[int, ...] = (0, 1), step: str = "query") -> CommandResult:
        return self.execute(args, cwd, step=step, allowed_returncodes=allowed_returncodes)
