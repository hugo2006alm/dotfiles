import os
from datetime import datetime
from pathlib import Path
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.execution import ExecutionContext

class RecorderAction(Action):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx
        self._pid_file = Path("/tmp/wf-recorder.pid")

    def execute(self, args: list[str]) -> None:
        is_running = False
        pid = None
        
        if self._pid_file.exists():
            try:
                pid = self._pid_file.read_text().strip()
                if pid:
                    res = self._exec.execute(["kill", "-0", pid])
                    if res.returncode == 0:
                        is_running = True
            except Exception:
                pass

        if not is_running:
            res_pgrep = self._exec.execute(["pgrep", "-f", "wf-recorder"])
            if res_pgrep.returncode == 0:
                is_running = True
                pid = res_pgrep.stdout.strip().split("\n")[0]

        if is_running and pid:
            self._exec.execute(["kill", "-INT", pid])
            if self._pid_file.exists():
                try:
                    self._pid_file.unlink()
                except Exception:
                    pass
            self._exec.execute(["pkill", "-RTMIN+9", "waybar"])
            self._exec.execute([
                "notify-send",
                "-i", "camera-video",
                "Screen Recording",
                "Recording stopped and saved"
            ])
        else:
            videos_res = self._exec.execute(["xdg-user-dir", "VIDEOS"])
            videos_dir = Path(videos_res.stdout.strip() or os.path.expanduser("~/Videos"))
            record_dir = videos_dir / "Recordings"
            
            if not self._exec.dry_run:
                record_dir.mkdir(parents=True, exist_ok=True)
                if self._pid_file.exists():
                    try:
                        self._pid_file.unlink()
                    except Exception:
                        pass

            filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".mkv"
            file_path = record_dir / filename

            if self._exec.dry_run:
                print(f"[DRY-RUN] Would start: wf-recorder -f {file_path}")
            else:
                import subprocess
                proc = subprocess.Popen(["wf-recorder", "-f", str(file_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._pid_file.write_text(str(proc.pid))
            
            self._exec.execute(["pkill", "-RTMIN+9", "waybar"])
            self._exec.execute([
                "notify-send",
                "-i", "camera-video",
                "Screen Recording",
                "Recording started…"
            ])
