import os
import subprocess
from datetime import datetime
from pathlib import Path
from uuid import uuid4
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.execution import ExecutionContext

class ScreenshotAction(Action):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def execute(self, args: list[str]) -> None:
        if any(arg != "--region" for arg in args):
            raise ValueError("Screenshot supports only --region")
        pictures_res = self._exec.optional(["xdg-user-dir", "PICTURES"])
        pictures_dir = Path(pictures_res.stdout.strip() or os.path.expanduser("~/Pictures"))
        screenshot_dir = pictures_dir / "Screenshots"
        
        filename = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + "_" + uuid4().hex[:8] + ".png"
        file_path = screenshot_dir / filename

        use_region = "--region" in args
        
        if use_region:
            slurp_res = self._exec.query(["slurp"])
            coords = slurp_res.stdout.strip()
            if not coords:
                return
            grim_cmd = ["grim", "-g", coords, str(file_path)]
        else:
            grim_cmd = ["grim", str(file_path)]

        if not self._exec.dry_run:
            screenshot_dir.mkdir(parents=True, exist_ok=True)
        try:
            self._exec.execute(grim_cmd, step="screenshot:capture")
        except BaseException:
            if not self._exec.dry_run:
                file_path.unlink(missing_ok=True)
            raise
        if self._exec.dry_run:
            print("[DRY-RUN] Would copy screenshot to clipboard")
            return
        try:
            with file_path.open("rb") as image:
                result = subprocess.run(["wl-copy", "--type", "image/png"], stdin=image,
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                        check=False, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError("Screenshot saved, but clipboard copy failed") from error
        if result.returncode:
            raise RuntimeError(f"Screenshot saved, but clipboard copy failed ({result.returncode})")
        self._exec.optional([
            "notify-send",
            "-i", str(file_path),
            "Screenshot copied",
            f"Saved to {filename}"
        ])
