import os
from pathlib import Path
from types import TracebackType
from typing import Type
from dotfiles_api.domain.contracts import FileWriter
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.application.store import ArtifactStore

class ConfigTransaction:
    def __init__(self, env: EnvironmentContext, store: ArtifactStore, writer: FileWriter, dry_run: bool = False) -> None:
        self._env = env
        self._store = store
        self._writer = writer
        self._dry_run = dry_run
        self._backups: dict[Path, str] = {}
        self.theme_name = ""

    def __enter__(self) -> "ConfigTransaction":
        self._backups.clear()
        return self

    def write_artifact(self, artifact: GeneratedArtifact) -> None:
        target_path = self._store.resolve_path(artifact.artifact_id, theme_name=self.theme_name)
        if self._dry_run:
            print(f"[DRY-RUN] Would write file {target_path} with content:\n{artifact.content}")
            return
        
        # System path grace check
        if str(target_path).startswith("/etc/"):
            if target_path.exists() and not os.access(target_path, os.W_OK):
                print(f"[WARNING] No write access to {target_path} — skipping system configuration.")
                return
            elif not target_path.exists():
                parent = target_path.parent
                if not parent.exists() or not os.access(parent, os.W_OK):
                    print(f"[WARNING] No write access to {parent} — skipping system configuration.")
                    return

        if target_path.exists() and target_path not in self._backups:
            self._backups[target_path] = target_path.read_text()
        self._writer.write(target_path, artifact.content)

    def __exit__(self, exc_type: Type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> bool:
        if exc_type is not None:
            for path, content in self._backups.items():
                try:
                    path.write_text(content)
                except Exception:
                    pass
            return False
        return True
