from pathlib import Path
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext

class ServicesSetupService:
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def setup_services(self) -> None:
        self._exec.execute(["sudo", "systemctl", "enable", "NetworkManager"])
        self._exec.execute(["sudo", "systemctl", "enable", "bluetooth"])
        self._exec.execute(["sudo", "systemctl", "enable", "sshd"])
        self._exec.execute(["sudo", "systemctl", "enable", "paccache.timer"])

        self._exec.execute(["systemctl", "--user", "enable", "--now", "pipewire", "pipewire-pulse", "wireplumber"])
        self._exec.execute(["sudo", "systemctl", "enable", "swayosd-libinput-backend"])

        self._exec.execute(["sudo", "ufw", "enable"])
        self._exec.execute(["sudo", "ufw", "default", "deny", "incoming"])
        self._exec.execute(["sudo", "ufw", "default", "allow", "outgoing"])

        self._exec.execute(["sudo", "mkdir", "-p", "/etc/greetd"])
        
        greet_conf_src = self._env.home_dir / ".config" / "greetd" / "hyprland-greet.conf"
        if not self._exec.dry_run and greet_conf_src.exists():
            self._exec.execute(["sudo", "cp", str(greet_conf_src), "/etc/greetd/hyprland-greet.conf"])
        
        self._exec.execute(["sudo", "touch", "/etc/greetd/regreet.toml"])
        self._exec.execute(["sudo", "chmod", "666", "/etc/greetd/regreet.toml"])
        self._exec.execute(["sudo", "touch", "/etc/greetd/regreet-background.jpg"])
        self._exec.execute(["sudo", "chmod", "666", "/etc/greetd/regreet-background.jpg"])
        self._exec.execute(["sudo", "touch", "/etc/greetd/regreet.css"])
        self._exec.execute(["sudo", "chmod", "666", "/etc/greetd/regreet.css"])
        self._exec.execute(["sudo", "chmod", "666", "/etc/greetd/hyprland-greet.conf"])

        greetd_config = """[terminal]
vt = 1

[default_session]
command = "Hyprland --config /etc/greetd/hyprland-greet.conf > /dev/null 2>&1"
user = "greeter"
"""
        self._sudo_write("/etc/greetd/config.toml", greetd_config)
        self._exec.execute(["sudo", "systemctl", "enable", "greetd"])

        desktop_file = "/usr/share/wayland-sessions/hyprland.desktop"
        self._exec.execute(["sudo", "sed", "-i", 's|^Exec=.*|Exec=/bin/sh -c "/usr/bin/start-hyprland > /dev/null 2>\\&1"|', desktop_file])

        sudoers_content = f"""{self._env.user} ALL=(ALL) NOPASSWD: /usr/bin/cp {self._env.home_dir}/.config/greetd/regreet.css /etc/greetd/regreet.css
{self._env.user} ALL=(ALL) NOPASSWD: /usr/bin/cp {self._env.home_dir}/dotfiles/.config/greetd/hyprland-greet.conf /etc/greetd/hyprland-greet.conf
"""
        self._sudo_write("/etc/sudoers.d/shade-raid", sudoers_content)
        self._exec.execute(["sudo", "chmod", "0440", "/etc/sudoers.d/shade-raid"])
        self._exec.execute(["sudo", "rm", "-f", "/etc/sudoers.d/plymouth_sync"])
        self._exec.execute(["sudo", "rm", "-f", "/etc/sudoers.d/regreet-theme"])

    def _sudo_write(self, target_path: str, content: str) -> None:
        if self._exec.dry_run:
            print(f"[DRY-RUN] Would write file {target_path} (via sudo) with content:\n{content}")
            return
        temp_path = Path("/tmp/shade-raid-sudo-temp")
        try:
            temp_path.write_text(content)
            self._exec.execute(["sudo", "cp", str(temp_path), target_path])
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
