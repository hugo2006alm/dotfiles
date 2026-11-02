from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext


class ServicesSetupService:
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def setup_services(self) -> None:
        for service in ["NetworkManager", "bluetooth", "sshd", "paccache.timer",
                        "swayosd-libinput-backend"]:
            self._exec.execute(["sudo", "systemctl", "enable", service])
        self._exec.execute(["systemctl", "--user", "enable", "--now",
                            "pipewire", "pipewire-pulse", "wireplumber"])
        self._exec.execute(["sudo", "ufw", "default", "deny", "incoming"])
        self._exec.execute(["sudo", "ufw", "default", "allow", "outgoing"])
        self._exec.execute(["sudo", "ufw", "enable"])
