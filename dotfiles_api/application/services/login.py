import sys
import tempfile
import tomllib
import uuid
from pathlib import Path

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext


class LoginSetupService:
    """Explicit installation of root-owned login files with a recovery snapshot."""

    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def apply(self) -> Path | None:
        if not self._exec.dry_run and not sys.stdin.isatty():
            raise RuntimeError("Login setup requires an interactive terminal; run dotfiles setup-login yourself.")

        source = self._env.home_dir / ".config" / "greetd"
        if Path("/etc/greetd").is_symlink() or Path("/var/backups/shade-raid").is_symlink():
            raise ValueError("Refusing linked login or backup directories; inspect them before installation.")
        files = {name: (source / name).read_text() for name in
                 ("hyprland-greet.conf", "regreet.toml", "regreet.css")}
        tomllib.loads(files["regreet.toml"])
        if any(not content.strip() for content in files.values()):
            raise ValueError("Login configuration is empty; run dotfiles configure first.")
        files["config.toml"] = '''[terminal]
vt = 1

[default_session]
command = "Hyprland --config /etc/greetd/hyprland-greet.conf"
user = "greeter"
'''
        tomllib.loads(files["config.toml"])
        if self._exec.dry_run:
            print("[DRY-RUN] Back up /etc/greetd and managed sudoers; install root:root 0644 login files; enable greetd.")
            return None

        backup_root = Path("/var/backups/shade-raid")
        backup = backup_root / uuid.uuid4().hex
        self._exec.execute(["sudo", "install", "-d", "-o", "root", "-g", "root",
                            "-m", "0700", str(backup_root), str(backup)])
        snapshot = '''set -eu
backup=$1
if [ -e /etc/greetd ] || [ -L /etc/greetd ]; then
    cp -a -- /etc/greetd "$backup/greetd"
else
    touch "$backup/greetd.absent"
fi
for name in shade-raid plymouth_sync regreet-theme; do
    path=/etc/sudoers.d/$name
    if [ -e "$path" ] || [ -L "$path" ]; then
        cp -a -- "$path" "$backup/sudoers.$name"
    fi
done
'''
        self._exec.execute(["sudo", "sh", "-c", snapshot, "shade-raid-backup", str(backup)])
        print(f"Login backup: {backup}")
        self._exec.execute(["sudo", "install", "-d", "-o", "root", "-g", "root",
                            "-m", "0755", "/etc/greetd"])
        with tempfile.TemporaryDirectory(prefix="shade-raid-login-") as temp:
            for name, content in files.items():
                staged = Path(temp) / name
                staged.write_text(content)
                staged.chmod(0o600)
                self._exec.execute(["sudo", "install", "-T", "-o", "root", "-g", "root",
                                    "-m", "0644", str(staged), str(Path("/etc/greetd") / name)])
        secure_background = '''set -eu
path=/etc/greetd/regreet-background.jpg
if [ -L "$path" ]; then
    echo "Refusing a linked login background; restore or replace it explicitly." >&2
    exit 1
fi
if [ -f "$path" ]; then
    chown root:root -- "$path"
    chmod 0644 -- "$path"
fi
'''
        self._exec.execute(["sudo", "sh", "-c", secure_background, "shade-raid-background"])
        self._exec.execute(["sudo", "rm", "-f", "--", "/etc/sudoers.d/shade-raid",
                            "/etc/sudoers.d/plymouth_sync", "/etc/sudoers.d/regreet-theme"])
        self._exec.execute(["sudo", "visudo", "-c"])
        self._exec.execute(["sudo", "systemctl", "enable", "greetd"])
        print("Login files installed. Keep a TTY open and verify login before rebooting.")
        return backup
