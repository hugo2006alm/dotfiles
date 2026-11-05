import threading
import fcntl
import os
import sys
from dotfiles_api.domain.contracts.reloadable import Reloadable, EventReloadable
from dotfiles_api.domain.events import ConfigGeneratedEvent, ReloadRequestedEvent

class ReloadService:
    def __init__(self, reloadables: list[Reloadable], verbose: bool = False,
                 optional_reloadables: list[Reloadable] | None = None, dry_run: bool = False) -> None:
        self._reloadables = reloadables
        self._verbose = verbose
        self._dry_run = dry_run
        self._optional = {id(item) for item in optional_reloadables or []}
        self._event_reloadables = [
            r for r in reloadables if isinstance(r, EventReloadable)
        ]
        self._thread_locks: dict[str, threading.Lock] = {}
        self._lock_creation_lock = threading.Lock()

    def _safe_reload(self, r: Reloadable) -> None:
        name = r.__class__.__name__
        lock_file = f"/tmp/dotfiles_reload_{name}.lock"
        pending_file = f"/tmp/dotfiles_reload_{name}.pending"

        # 1. Get or create thread lock
        with self._lock_creation_lock:
            if name not in self._thread_locks:
                self._thread_locks[name] = threading.Lock()
            t_lock = self._thread_locks[name]

        # 2. Acquire thread lock
        if not t_lock.acquire(blocking=False):
            raise RuntimeError(f"Refresh for {name} is already running; retry after it finishes")

        # 3. Acquire process file lock
        f = None
        try:
            f = open(lock_file, "w")
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            t_lock.release()
            if f:
                f.close()
            raise RuntimeError(f"Refresh for {name} is already running; retry after it finishes") from None
        except Exception:
            # Fallback in case of disk permission issues
            pass

        # 4. Loop to execute the reload and check pending flag
        try:
            while True:
                if self._verbose:
                    print(f"[VERBOSE] Executing reload method for: {name}")
                r.reload()
                
                if os.path.exists(pending_file):
                    try:
                        os.remove(pending_file)
                    except Exception:
                        pass
                    if self._verbose:
                        print(f"[VERBOSE] Pending reload flag found for {name}. Repeating execution.")
                    continue
                break
        finally:
            # 5. Clean up locks
            try:
                if f:
                    f.close()
                if os.path.exists(lock_file):
                    os.remove(lock_file)
            except Exception:
                pass
            t_lock.release()

    def _reload(self, reloadables: list[Reloadable]) -> None:
        if self._dry_run:
            print(f"[DRY-RUN] Would refresh {len(reloadables)} application handlers")
            return
        errors = []
        for reloadable in reloadables:
            name = reloadable.__class__.__name__
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

    def reload_all(self) -> None:
        if self._verbose:
            print(f"[VERBOSE] Reloading all {len(self._reloadables)} reloadables synchronously")
        self._reload(self._reloadables)

    def handle_config_generated(self, event: ConfigGeneratedEvent) -> None:
        if self._verbose:
            print(f"[VERBOSE] Received ConfigGeneratedEvent for generator: {event.generator_name}")
        self._reload([r for r in self._event_reloadables if r.supports(event.generator_name)])

    def handle_reload_requested(self, event: ReloadRequestedEvent) -> None:
        self.reload_all()
