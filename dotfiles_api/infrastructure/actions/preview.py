from dotfiles_api.domain.contracts.action import Action
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.application.preview_transaction import preview_transaction, restore_preview
from dotfiles_api.application.validation import ArtifactValidator
from dotfiles_api.infrastructure.file_store import FileThemeStore
from dotfiles_api.infrastructure.generators.swaync import SwayncGenerator
from dotfiles_api.infrastructure.runtime_lock import RuntimeLock


class PreviewAction(Action):
    def __init__(self, exec_ctx, env):
        self._exec, self._env = exec_ctx, env

    def execute(self, args):
        if len(args) != 1 or args[0] not in {"next", "prev"}:
            raise ValueError("Preview requires next or prev")
        themes_dir = self._env.home_dir / ".config/themes"
        themes = sorted(item.name for item in themes_dir.iterdir()
                        if item.is_dir() and (item / "colors.toml").is_file()) if themes_dir.is_dir() else []
        if not themes:
            return
        if self._exec.dry_run:
            print("[DRY-RUN] Would preview the next/previous theme and refresh SwayNC")
            return
        with RuntimeLock(self._env.lock_dir / "configure.lock"):
            preview = self._env.preview_file
            current = preview.read_text().strip() if preview.is_file() else ""
            active = FileThemeStore(self._env).get_active_theme()
            current = current if current in themes else active if active in themes else themes[0]
            selected = themes[(themes.index(current) + (1 if args[0] == "next" else -1)) % len(themes)]
            # Roll back the preceding overlay first, including any interrupted preview.
            restore_preview(self._env)
            active = active if active in themes else themes[0]
            tokens = ThemeLoader(self._env).load(active)
            tx = preview_transaction(self._env)
            tx.theme_name = active
            tx.generators = ["swaync"]
            artifacts = SwayncGenerator(transaction=tx, preview_theme=selected).render(tokens, active)
            artifacts.append(GeneratedArtifact("theme-preview", selected))
            for artifact in artifacts:
                path = tx._store.resolve_path(artifact.artifact_id, theme_name=active)
                self._env.validate_output_path(path)
                ArtifactValidator().validate(path, artifact.content)
            with tx:
                for artifact in artifacts:
                    tx.write_artifact(artifact)
        self._exec.execute(["swaync-client", "-R"], step="preview:reload-config")
        self._exec.execute(["swaync-client", "-rs"], step="preview:reload-style")
