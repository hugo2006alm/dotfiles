import os


class WaylandSessionService:
    """Prepare activation once, then let user systemd own persistent processes."""

    VARIABLES = ("WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "XDG_SESSION_TYPE",
                 "HYPRLAND_INSTANCE_SIGNATURE", "DISPLAY", "XAUTHORITY", "PATH", "XDG_DATA_DIRS",
                 "QT_QPA_PLATFORMTHEME")

    def __init__(self, execution, applications=None):
        self.execution, self.applications = execution, applications

    def _prepare_environment(self):
        if not self.execution.dry_run and not all(os.environ.get(key) for key in
                                                  ("WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP")):
            raise RuntimeError("A Wayland session with WAYLAND_DISPLAY and XDG_CURRENT_DESKTOP is required")
        variables = [key for key in self.VARIABLES if os.environ.get(key)]
        if self.execution.dry_run:
            variables = list(self.VARIABLES)
        self.execution.execute(["dbus-update-activation-environment", "--systemd", *variables],
                               step="session:environment")

    def ensure_portals(self):
        self._prepare_environment()
        self._start_portal()

    def _start_portal(self):
        self.execution.execute(["systemctl", "--user", "start", "xdg-desktop-portal.service"],
                               step="session:portal")

    def start(self):
        self._prepare_environment()
        self.execution.execute(["systemctl", "--user", "daemon-reload"], step="session:units")
        units = [spec.user_unit for spec in self.applications.specs if spec.user_unit] if self.applications else []
        if units:
            self.execution.execute(["systemctl", "--user", "start", *units], step="session:start")
        self._start_portal()
