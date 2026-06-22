import os
import shutil
from pathlib import Path
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext

class UserSetupService:
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env

    def setup_user(self, setup_github: bool = False) -> None:
        name_res = self._exec.execute(["git", "config", "--global", "user.name"])
        email_res = self._exec.execute(["git", "config", "--global", "user.email"])
        
        git_name = name_res.stdout.strip()
        git_email = email_res.stdout.strip()

        if not git_name or not git_email:
            if not self._exec.dry_run:
                print("==> Setting up git...")
                try:
                    name_input = input("Git name [Press Enter to skip]: ").strip()
                    email_input = input("Git email [Press Enter to skip]: ").strip()
                    if name_input:
                        self._exec.execute(["git", "config", "--global", "user.name", name_input])
                    if email_input:
                        self._exec.execute(["git", "config", "--global", "user.email", email_input])
                except (IOError, EOFError):
                    pass
        
        self._exec.execute(["git", "config", "--global", "core.pager", "delta"])
        self._exec.execute(["chsh", "-s", "/usr/bin/fish"])
        self._exec.execute(["xdg-user-dirs-update"])
        self._exec.execute(["fc-cache", "-fv"])

        for f in [".bash_history", ".bash_logout", ".bash_profile", ".bashrc"]:
            path = self._env.home_dir / f
            if path.exists():
                if self._exec.dry_run:
                    print(f"[DRY-RUN] Would remove: {path}")
                else:
                    try:
                        path.unlink()
                    except Exception:
                        pass

        self._exec.execute([
            "sudo", "reflector", "--latest", "20",
            "--protocol", "https", "--sort", "rate",
            "--save", "/etc/pacman.d/mirrorlist"
        ])

        self._exec.execute(["mise", "install", "python@latest"])

        pictures_dir = self._env.home_dir / "Pictures"
        videos_dir = self._env.home_dir / "Videos"
        downloads_dir = self._env.home_dir / "Downloads"
        documents_dir = self._env.home_dir / "Documents"
        music_dir = self._env.home_dir / "Music"
        desktop_dir = self._env.home_dir / "Desktop"

        if not self._exec.dry_run:
            (pictures_dir / "Screenshots").mkdir(parents=True, exist_ok=True)
            (videos_dir / "Recordings").mkdir(parents=True, exist_ok=True)
            (self._env.home_dir / "wallpapers" / "shade-raid").mkdir(parents=True, exist_ok=True)

        gtk_dir = self._env.home_dir / ".config" / "gtk-3.0"
        bookmarks_content = f"""file://{downloads_dir} Downloads
file://{documents_dir} Documents
file://{pictures_dir} Pictures
file://{music_dir} Music
file://{videos_dir} Videos
file://{desktop_dir} Desktop
"""
        if self._exec.dry_run:
            print(f"[DRY-RUN] Would write bookmarks at {gtk_dir / 'bookmarks'} with:\n{bookmarks_content}")
        else:
            gtk_dir.mkdir(parents=True, exist_ok=True)
            (gtk_dir / "bookmarks").write_text(bookmarks_content)

        self._exec.execute([
            "fish", "-c",
            "curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fisher && fisher update"
        ])

        if setup_github:
            self._exec.execute(["gh", "auth", "login"])

        personal_autostart = self._env.home_dir / ".config" / "hypr" / "autostart-personal.lua"
        autostart_example = self._env.home_dir / ".config" / "hypr" / "autostart-personal.lua.example"
        if not personal_autostart.exists() and autostart_example.exists():
            if self._exec.dry_run:
                print(f"[DRY-RUN] Would copy {autostart_example} to {personal_autostart}")
            else:
                try:
                    shutil.copy(str(autostart_example), str(personal_autostart))
                except Exception:
                    pass
