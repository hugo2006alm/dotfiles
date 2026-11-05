import os
from dotfiles_api.infrastructure.ssh_agent import select_agent


class WaylandSessionService:
    """Prepare activation once, then let user systemd own persistent processes."""

    VARIABLES = ("WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "XDG_SESSION_TYPE",
                 "HYPRLAND_INSTANCE_SIGNATURE", "DISPLAY", "XAUTHORITY", "PATH", "XDG_DATA_DIRS",
                 "QT_QPA_PLATFORMTHEME", "SSH_AUTH_SOCK")

    def __init__(self, execution, applications=None):
        self.execution, self.applications = execution, applications

    def _prepare_environment(self):
        if not self.execution.dry_run and not all(os.environ.get(key) for key in
                                                  ("WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP")):
            raise RuntimeError("A Wayland session with WAYLAND_DISPLAY and XDG_CURRENT_DESKTOP is required")
        external_agent = select_agent() if not self.execution.dry_run else False
        variables = [key for key in self.VARIABLES if os.environ.get(key)]
        if self.execution.dry_run:
            variables = list(self.VARIABLES)
        self.execution.execute(["dbus-update-activation-environment", "--systemd", *variables],
                               step="session:environment")
        return external_agent

    def ensure_portals(self):
        self._prepare_environment()
        self._start_portal()

    def _start_portal(self):
        self.execution.execute(["systemctl", "--user", "start", "xdg-desktop-portal.service"],
                               step="session:portal")

    def start(self):
        external_agent = self._prepare_environment()
        failures = []
        try:
            self.execution.execute(["systemctl", "--user", "daemon-reload"], step="session:units")
        except Exception as error:
            failures.append(f"daemon-reload: {error}")
        else:
            units = [spec.user_unit for spec in self.applications.specs if spec.user_unit] if self.applications else []
            if external_agent:
                units = [unit for unit in units if unit != "shade-raid-ssh-agent.service"]
            for unit in units:
                try:
                    self.execution.execute(["systemctl", "--user", "start", unit], step=f"session:start:{unit}")
                except Exception as error:
                    failures.append(f"{unit}: {error}")
        try:
            self._start_portal()
        except Exception as error:
            failures.append(f"xdg-desktop-portal.service: {error}")
        if failures:
            raise RuntimeError("Wayland session startup failed: " + "; ".join(failures))
