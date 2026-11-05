import shutil
import os
from pathlib import Path
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.context.environment import EnvironmentContext

class ExtrasSetupService:
    def __init__(self, exec_ctx: ExecutionContext, env: EnvironmentContext) -> None:
        self._exec = exec_ctx
        self._env = env
        self._spotify_path = Path("/opt/spotify")
        self._prefs_path = self._env.home_dir / ".config" / "spotify" / "prefs"

    def setup_extras(self) -> None:
        if not shutil.which("spotify") and not self._spotify_path.exists():
            print("Spotify not installed, skipping Spicetify setup.")
            return

        if not shutil.which("spicetify"):
            print("Spicetify CLI not installed, skipping Spicetify setup.")
            return

        if not self._prefs_path.exists():
            print(f"Spotify prefs not found at {self._prefs_path}. Launch Spotify once, then run setup again.")
            return

        apps = self._spotify_path / "Apps"
        if not os.access(self._spotify_path, os.W_OK) or (apps.exists() and not os.access(apps, os.W_OK)):
            print("Spotify is not user-writable; skipping optional Spicetify customization.")
            return

        if self._exec.optional(["spicetify", "backup", "apply"]).returncode:
            return
        if self._exec.optional(["spicetify", "refresh", "-a", "-e"]).returncode:
            return
        self._exec.optional(["spicetify", "apply"])
