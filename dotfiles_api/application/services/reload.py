import sys
from pathlib import Path
from dotfiles_api.infrastructure.runtime_lock import RuntimeLock
from dotfiles_api.domain.contracts.reloadable import Reloadable, EventReloadable
from dotfiles_api.domain.events import ConfigGeneratedEvent, ReloadRequestedEvent


class ReloadService:
    def __init__(self, reloadables: list[Reloadable], verbose: bool = False,
                 dry_run: bool = False, runtime_dir: Path | None = None,
                 optional_reloadables: list[Reloadable] | None = None) -> None:
        self._reloadables = reloadables
        self._verbose = verbose
        self._dry_run = dry_run
        self._runtime_dir = runtime_dir or Path.home() / ".local/state/shade-raid/runtime"
        self._optional = {id(item) for item in optional_reloadables or []}
        self._event_reloadables = [r for r in reloadables if isinstance(r, EventReloadable)]

    def _safe_reload(self, reloadable: Reloadable) -> None:
        name = type(reloadable).__name__
        with RuntimeLock(self._runtime_dir / f"reload-{name}.lock"):
            reloadable.reload()

    def _reload(self, reloadables: list[Reloadable]) -> None:
        if self._dry_run:
            print(f"[DRY-RUN] Would refresh {len(reloadables)} application handlers")
            return
        errors = []
        for reloadable in reloadables:
            name = type(reloadable).__name__
            try:
                self._safe_reload(reloadable)
            except Exception as error:
                if id(reloadable) in self._optional:
                    print(f"[OPTIONAL] Refresh failed for {name}: {error}", file=sys.stderr)
                else:
                    errors.append((name, error))
        if errors:
            summary = "; ".join(f"{name}: {error}" for name, error in errors)
            raise RuntimeError(f"{len(errors)} required refreshes failed: {summary}")

    def reload_changed(self, generators) -> None:
        selected = [r for r in self._event_reloadables if any(r.supports(name) for name in generators)]
        try:
            self._reload(selected)
        except Exception as error:
            raise RuntimeError(f"Theme files committed; refresh failed: {error}. Run dotfiles reload or dotfiles rollback.") from error

    def reload_all(self) -> None:
        self._reload(self._reloadables)

    def handle_config_generated(self, event: ConfigGeneratedEvent) -> None:
        self._reload([r for r in self._event_reloadables if r.supports(event.generator_name)])

    def handle_reload_requested(self, event: ReloadRequestedEvent) -> None:
        self.reload_all()
