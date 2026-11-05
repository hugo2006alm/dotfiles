import json
import os
import select
import signal
import subprocess
import time
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

    def _wait_ready(self, process, output, timeout=10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Recorder exited before writing output; inspect {output}")
            if output.is_file() and output.stat().st_size > 0:
                return
            time.sleep(0.05)
        raise RuntimeError(f"Recorder did not produce output before timeout; inspect {output}")

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
                # Hold a kernel reference to the exact process before verifying identity again;
                # a reused numeric PID can never receive this signal.
                if not hasattr(os, "pidfd_open") or not hasattr(signal, "pidfd_send_signal"):
                    raise RuntimeError("Safe recorder stop requires Linux pidfd support")
                try:
                    pidfd = os.pidfd_open(record["pid"])
                except ProcessLookupError:
                    raise RuntimeError("Recorder exited before it could be stopped; inspect the recording") from None
                try:
                    if self._identity(record["pid"]) != record["identity"]:
                        raise RuntimeError("Recorder process changed before stop; no signal sent")
                    signal.pidfd_send_signal(pidfd, signal.SIGINT)
                    poller = select.poll()
                    poller.register(pidfd, select.POLLIN)
                    if not poller.poll(5000):
                        self._exec.optional(["notify-send", "Screen Recording", "Recorder is still finalizing; check again"])
                        return
                finally:
                    os.close(pidfd)
                self._pid_file.unlink(missing_ok=True)
                output = record.get("output")
                if not isinstance(output, str) or not Path(output).is_file() or Path(output).stat().st_size == 0:
                    raise RuntimeError("Recorder stopped without a nonempty output file; inspect recorder.log")
                self._exec.optional(["notify-send", "Screen Recording", "Recorder stopped; verify the output file"])
                return
            if isinstance(record, dict) and record.get("pid") and record.get("identity"):
                self._pid_file.unlink(missing_ok=True)
                raise RuntimeError("Previous recorder is no longer active; inspect its output and retry to start a new recording")
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
                    self._wait_ready(process, output)
                    SystemFileWriter().write(self._pid_file, json.dumps({"pid": process.pid, "identity": identity, "output": str(output)}))
                else:
                    raise RuntimeError(f"Recorder exited ({code}): " + log.read_text(errors="replace")[-500:])
            except BaseException:
                with suppress(OSError):
                    process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    with suppress(OSError):
                        process.kill()
                    with suppress(subprocess.TimeoutExpired):
                        process.wait(timeout=1)
                self._pid_file.unlink(missing_ok=True)
                raise
            self._exec.optional(["notify-send", "Screen Recording", "Recording started"])
