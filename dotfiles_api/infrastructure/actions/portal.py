import time
from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.context.execution import ExecutionContext

class PortalAction(Action):
    def __init__(self, exec_ctx: ExecutionContext) -> None:
        self._exec = exec_ctx

    def execute(self, args: list[str]) -> None:
        time.sleep(0.5)
        self._exec.execute(["killall", "-e", "xdg-desktop-portal-hyprland"])
        self._exec.execute(["killall", "-e", "xdg-desktop-portal-gnome"])
        self._exec.execute(["killall", "-e", "xdg-desktop-portal-kde"])
        self._exec.execute(["killall", "-e", "xdg-desktop-portal-lxqt"])
        self._exec.execute(["killall", "-e", "xdg-desktop-portal-wlr"])
        self._exec.execute(["killall", "xdg-desktop-portal"])

        if self._exec.dry_run:
            print("[DRY-RUN] Would start: /usr/lib/xdg-desktop-portal-hyprland")
        else:
            import subprocess
            try:
                subprocess.Popen(["/usr/lib/xdg-desktop-portal-hyprland"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        
        time.sleep(1.0)

        if self._exec.dry_run:
            print("[DRY-RUN] Would start: /usr/lib/xdg-desktop-portal")
        else:
            import subprocess
            try:
                subprocess.Popen(["/usr/lib/xdg-desktop-portal"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
