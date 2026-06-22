import os
from datetime import datetime
from pathlib import Path
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.execution import ExecutionContext

class ScreenshotAction(Action):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def execute(self, args: list[str]) -> None:
        pictures_res = self._exec.execute(["xdg-user-dir", "PICTURES"])
        pictures_dir = Path(pictures_res.stdout.strip() or os.path.expanduser("~/Pictures"))
        screenshot_dir = pictures_dir / "Screenshots"
        
        if not self._exec.dry_run:
            screenshot_dir.mkdir(parents=True, exist_ok=True)

        filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        file_path = screenshot_dir / filename

        use_region = "--region" in args
        
        if use_region:
            slurp_res = self._exec.execute(["slurp"])
            coords = slurp_res.stdout.strip()
            if not coords:
                return
            grim_cmd = ["grim", "-g", coords, str(file_path)]
        else:
            grim_cmd = ["grim", str(file_path)]

        self._exec.execute(grim_cmd)
        self._exec.execute(["bash", "-c", f"wl-copy < {file_path}"])
        self._exec.execute([
            "notify-send",
            "-i", str(file_path),
            "Screenshot copied",
            f"Saved to {filename}"
        ])
