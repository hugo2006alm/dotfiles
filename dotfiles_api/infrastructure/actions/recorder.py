import json
import os
import subprocess
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.infrastructure.runtime_lock import RuntimeLock
from dotfiles_api.infrastructure.file_writer import SystemFileWriter


class RecorderAction(Action):
    def __init__(self, exec_ctx, env=None):
        self._exec = exec_ctx
        self.env = env or EnvironmentContext(Path.home(), Path.home() / "dotfiles", "")
        self._pid_file = self.env.runtime_dir / "recorder.pid"

    def _identity(self, pid):
        if not isinstance(pid, int) or pid <= 1:
            return None
        try:
            proc = Path("/proc") / str(pid)
            if proc.stat().st_uid != os.getuid() or (proc / "comm").read_text().strip() != "wf-recorder":
                return None
            fields = (proc / "stat").read_text().rsplit(")", 1)[1].split()
            return str(os.getuid()) + ":" + fields[19]
        except (OSError, IndexError):
            return None

    def execute(self, args):
        if args:
            raise ValueError("Recording action takes no arguments")
        if self._exec.dry_run:
            print("[DRY-RUN] Would start/stop the managed recorder; no PID or process changes")
            return
        self.env.validate_output_path(self._pid_file)
        lock = self.env.runtime_dir / "recorder.lock"
        self.env.validate_output_path(lock)
        with RuntimeLock(lock):
            record = {}
            if self._pid_file.exists():
                try:
                    record = json.loads(self._pid_file.read_text())
                except (ValueError, OSError):
                    pass
            if isinstance(record, dict) and record.get("identity") and self._identity(record.get("pid")) == record["identity"]:
                self._exec.execute(["kill", "-INT", str(record["pid"])], step="recorder:stop")
                self._exec.optional(["notify-send", "Screen Recording", "Stop requested; recorder is finalizing"])
                return
            self._pid_file.unlink(missing_ok=True)
            result = self._exec.optional(["xdg-user-dir", "VIDEOS"])
            directory = Path(result.stdout.strip() or str(self.env.home_dir / "Videos")) / "Recordings"
            directory.mkdir(parents=True, exist_ok=True)
            name = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_" + uuid4().hex[:8] + ".mkv"
            output = directory / name
            log = self.env.runtime_dir / "recorder.log"
            self.env.validate_output_path(log)
            fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0), 0o600)
            with os.fdopen(fd, "wb") as stream:
                process = subprocess.Popen(["wf-recorder", "-f", str(output)], stdout=subprocess.DEVNULL, stderr=stream)
            try:
                try:
                    code = process.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    identity = self._identity(process.pid)
                    if not identity:
                        raise RuntimeError("Recorder not running after startup; inspect " + str(log))
                    SystemFileWriter().write(self._pid_file, json.dumps({"pid": process.pid, "identity": identity, "output": str(output)}))
                else:
                    output.unlink(missing_ok=True)
                    raise RuntimeError(f"Recorder exited ({code}): " + log.read_text(errors="replace")[-500:])
            except BaseException:
                with suppress(OSError):
                    process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    with suppress(OSError):
                        process.kill()
                self._pid_file.unlink(missing_ok=True)
                raise
            self._exec.optional(["notify-send", "Screen Recording", "Recording started"])
