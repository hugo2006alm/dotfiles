import shutil
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

        self._exec.execute(["sudo", "chmod", "a+wr", str(self._spotify_path)])
        self._exec.execute(["sudo", "chmod", "-R", "a+wr", str(self._spotify_path / "Apps")])

        self._exec.execute(["spicetify", "backup", "apply"])
        self._exec.execute([
            "bash", "-c",
            "curl -fsSL https://raw.githubusercontent.com/spicetify/marketplace/main/resources/install.sh | bash"
        ])
        self._exec.execute(["spicetify", "refresh", "-a", "-e"])
        self._exec.execute(["spicetify", "apply"])
