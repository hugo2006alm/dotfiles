import threading
import fcntl
import os
from pathlib import Path
from dotfiles_api.infrastructure.runtime_lock import RuntimeLock
from dotfiles_api.domain.contracts.reloadable import Reloadable, EventReloadable
from dotfiles_api.domain.events import ConfigGeneratedEvent, ReloadRequestedEvent

class ReloadService:
    def __init__(self, reloadables: list[Reloadable], verbose: bool = False, dry_run: bool = False, runtime_dir: Path | None = None) -> None:
        self._reloadables = reloadables
        self._verbose = verbose
        self._dry_run = dry_run
        self._runtime_dir = runtime_dir or Path.home() / ".local/state/shade-raid/runtime"
        self._event_reloadables = [
            r for r in reloadables if isinstance(r, EventReloadable)
        ]
        self._thread_locks: dict[str, threading.Lock] = {}
        self._lock_creation_lock = threading.Lock()

    def _safe_reload(self, reloadable: Reloadable) -> None:
        name = reloadable.__class__.__name__
        with RuntimeLock(self._runtime_dir / f"reload-{name}.lock"):
            reloadable.reload()

    def reload_changed(self, generators) -> None:
        if self._dry_run:
            return
        for reloadable in self._event_reloadables:
            if any(reloadable.supports(name) for name in generators):
                try:
                    self._safe_reload(reloadable)
                except Exception as error:
                    raise RuntimeError(f"Theme files committed; refresh failed for {type(reloadable).__name__}. "
                                       "Run dotfiles reload or dotfiles rollback.") from error

    def reload_all(self) -> list[threading.Thread]:
        if self._dry_run:
            print(f"[DRY-RUN] Would reload {len(self._reloadables)} application handlers")
            return []
        if self._verbose:
            print(f"[VERBOSE] Reloading all {len(self._reloadables)} reloadables in parallel threads")
        threads = []
        for reloadable in self._reloadables:
            if self._verbose:
                print(f"[VERBOSE] Spawning reload thread for: {reloadable.__class__.__name__}")
            t = threading.Thread(target=self._safe_reload, args=(reloadable,))
            t.start()
            threads.append(t)
        return threads

    def handle_config_generated(self, event: ConfigGeneratedEvent) -> list[threading.Thread]:
        if self._dry_run:
            print(f"[DRY-RUN] Would refresh {event.generator_name}")
            return []
        if self._verbose:
            print(f"[VERBOSE] Received ConfigGeneratedEvent for generator: {event.generator_name}")
        threads = []
        for r in self._event_reloadables:
            if r.supports(event.generator_name):
                if self._verbose:
                    print(f"[VERBOSE] Spawning reload thread for: {r.__class__.__name__}")
                t = threading.Thread(target=self._safe_reload, args=(r,))
                t.start()
                threads.append(t)
        return threads

    def handle_reload_requested(self, event: ReloadRequestedEvent) -> None:
        self.reload_all()
