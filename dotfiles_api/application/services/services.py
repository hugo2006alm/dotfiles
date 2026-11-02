from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext


class ServicesSetupService:
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def setup_services(self, enable_ssh_server: bool = False) -> None:
        for service in ["NetworkManager", "bluetooth", "paccache.timer",
                        "swayosd-libinput-backend"]:
            self._exec.execute(["sudo", "systemctl", "enable", service])
        self._exec.execute(["systemctl", "--user", "enable", "--now",
                            "pipewire", "pipewire-pulse", "wireplumber"])
        self._exec.execute(["sudo", "ufw", "default", "deny", "incoming"])
        self._exec.execute(["sudo", "ufw", "default", "allow", "outgoing"])
        if enable_ssh_server:
            self._exec.execute(["sudo", "ufw", "allow", "ssh"])
            self._exec.execute(["sudo", "systemctl", "enable", "sshd"])
        self._exec.execute(["sudo", "ufw", "enable"])
