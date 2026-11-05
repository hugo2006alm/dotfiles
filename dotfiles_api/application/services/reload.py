import sys
import os
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
from pathlib import Path
from dotfiles_api.infrastructure.runtime_lock import RuntimeLock
from dotfiles_api.domain.contracts.reloadable import Reloadable, EventReloadable
from dotfiles_api.domain.events import ConfigGeneratedEvent, ReloadRequestedEvent


class ReloadService:
    def __init__(self, reloadables: list[Reloadable], verbose: bool = False,
                 dry_run: bool = False, runtime_dir: Path | None = None,
                 optional_reloadables: list[Reloadable] | None = None, pending_path: Path | None = None,
                 output_guard=None) -> None:
        self._reloadables = reloadables
        self._verbose = verbose
        self._dry_run = dry_run
        self._runtime_dir = runtime_dir or Path.home() / ".local/state/shade-raid/runtime"
        self._optional = {id(item) for item in optional_reloadables or []}
        self._pending_path = pending_path
        self._output_guard = output_guard
        self._event_reloadables = [r for r in reloadables if isinstance(r, EventReloadable)]

    def _safe_reload(self, reloadable: Reloadable) -> None:
        name = type(reloadable).__name__
        with RuntimeLock(self._runtime_dir / f"reload-{name}.lock", blocking=False):
            reloadable.reload()

    def _reload(self, reloadables: list[Reloadable]) -> None:
        if self._dry_run:
            print(f"[DRY-RUN] Would refresh {len(reloadables)} application handlers")
            return
        errors = []
        for reloadable in reloadables:
            name = type(reloadable).__name__
            if self._verbose:
                print(f"[VERBOSE] Reloading: {name}")
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

    def _defer_offline(self) -> bool:
        if self._pending_path is None or os.environ.get("WAYLAND_DISPLAY"):
            return False
        if not self._dry_run:
            if self._output_guard:
                self._output_guard(self._pending_path)
            SystemFileWriter().write(self._pending_path, "refresh required\n")
            print("Desktop refresh pending; run dotfiles reload in a Wayland session.")
        return True

    def reload_changed(self, generators) -> None:
        selected = [r for r in self._event_reloadables if any(r.supports(name) for name in generators)]
        if selected and self._defer_offline():
            return
        try:
            self._reload(selected)
        except Exception as error:
            raise RuntimeError(f"Theme files committed; refresh failed: {error}. Run dotfiles reload or dotfiles rollback.") from error

    def reload_all(self) -> None:
        if self._defer_offline():
            return
        if self._verbose:
            print(f"[VERBOSE] Reloading all {len(self._reloadables)} reloadables synchronously")
        self._reload(self._reloadables)
        if self._pending_path is not None and not self._dry_run:
            if self._output_guard:
                self._output_guard(self._pending_path)
            self._pending_path.unlink(missing_ok=True)

    def handle_config_generated(self, event: ConfigGeneratedEvent) -> None:
        self._reload([r for r in self._event_reloadables if r.supports(event.generator_name)])

    def handle_reload_requested(self, event: ReloadRequestedEvent) -> None:
        self.reload_all()
