from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
import sys
import subprocess
from collections.abc import Callable
from dotfiles_api.domain.contracts import CommandExecutor, CommandResult
from dotfiles_api.context.command_error import CommandExecutionError
from dotfiles_api.context.command_logging import redacted_diagnostics
from dotfiles_api.domain.contracts.process_handle import ProcessHandle

@dataclass(frozen=True)
class ExecutionContext:
    dry_run: bool
    executor: CommandExecutor
    verbose: bool = False
    log_path: Path | None = None
    output_guard: Callable[[Path], None] | None = None

    def execute(self, args: list[str], cwd: Path | None = None, *,
                step: str = "command", allowed_returncodes: tuple[int, ...] = (0,),
                required: bool = True, sensitive: bool = False) -> CommandResult:
        command, _ = redacted_diagnostics(args, sensitive=sensitive)
        if self.dry_run:
            print(f"[DRY-RUN] Would execute: {command}")
            return CommandResult(stdout="", stderr="", returncode=0)
        if self.log_path is not None and self.output_guard is not None:
            self.output_guard(self.log_path)
        if self.verbose:
            print(f"[VERBOSE] Executing command: {command}")
        res = self.executor.execute(args, cwd)
        _, diagnostic = redacted_diagnostics(args, res.stderr or "", sensitive=sensitive)
        if not res.output_captured:
            diagnostic = "Output was inherited by the terminal; stderr was not captured"
        failed = res.returncode not in allowed_returncodes
        self._record(command, step, res.returncode, required, diagnostic if failed else "")
        if failed:
            error = CommandExecutionError(command, res.returncode, diagnostic or "see command output", step)
            if required:
                raise error
            print(f"[OPTIONAL] {error}", file=sys.stderr)
        return res

    def _record(self, command: str, step: str, returncode: int | None,
                required: bool, diagnostic: str, *, pid: int | None = None) -> None:
        if self.log_path is None:
            return
        try:
            if self.output_guard is not None:
                self.output_guard(self.log_path)
            self._write_record(command, step, returncode, required, diagnostic, pid)
        except (OSError, ValueError):
            # Observability failure must not replace the operation's result.
            print("[OBSERVABILITY] Command log unavailable; operational status preserved", file=sys.stderr)

    def _write_record(self, command: str, step: str, returncode: int | None,
                      required: bool, diagnostic: str, pid: int | None) -> None:
        if self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            record = {"time": datetime.now(timezone.utc).isoformat(), "command": command,
                      "step": step, "returncode": returncode,
                      "required": required, "diagnostic": diagnostic}
            if pid is not None:
                record["pid"] = pid
            flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(self.log_path, flags, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(json.dumps(record) + "\n")

    def spawn(self, args: list[str], cwd: Path | None = None, *,
              step: str = "launch", sensitive: bool = True) -> ProcessHandle | None:
        """Launch without pipes, observe startup briefly, and return lifecycle.

        A return means spawned/survived this observation, not ready or successful
        for its whole lifetime. The caller owns later polling/wait/cleanup.
        """
        command, _ = redacted_diagnostics(args, sensitive=sensitive)
        if self.dry_run:
            print(f"[DRY-RUN] Would launch: {command}")
            return None
        if self.verbose:
            print(f"[VERBOSE] Launching command: {command}")
        try:
            process = self.executor.spawn(args, cwd)
        except (OSError, RuntimeError):
            diagnostic = "Process could not be spawned; private output was not captured"
            self._record(command, step, 127, True, diagnostic)
            raise CommandExecutionError(command, 127, diagnostic, step) from None
        try:
            code = process.wait(timeout=0.1)
        except subprocess.TimeoutExpired:
            code = None
        diagnostic = "Process exited during startup; private output was not captured" if code else ""
        self._record(command, step, code, True, diagnostic, pid=process.pid)
        if code is not None and code != 0:
            raise CommandExecutionError(command, code, diagnostic, step)
        return process

    def optional(self, args: list[str], cwd: Path | None = None, *, step: str = "optional",
                 sensitive: bool = False) -> CommandResult:
        return self.execute(args, cwd, step=step, required=False, sensitive=sensitive)

    def query(self, args: list[str], cwd: Path | None = None, *,
              allowed_returncodes: tuple[int, ...] = (0, 1), step: str = "query",
              sensitive: bool = False) -> CommandResult:
        return self.execute(args, cwd, step=step, allowed_returncodes=allowed_returncodes, sensitive=sensitive)
