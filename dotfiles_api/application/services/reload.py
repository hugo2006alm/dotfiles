import threading
import fcntl
import os
from dotfiles_api.domain.contracts.reloadable import Reloadable, EventReloadable
from dotfiles_api.domain.events import ConfigGeneratedEvent, ReloadRequestedEvent

class ReloadService:
    def __init__(self, reloadables: list[Reloadable], verbose: bool = False) -> None:
        self._reloadables = reloadables
        self._verbose = verbose
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
            try:
                with open(pending_file, "w") as pf:
                    pf.write("1")
            except Exception:
                pass
            if self._verbose:
                print(f"[VERBOSE] Reload for {name} is already running in this process. Queued.")
            return

        # 3. Acquire process file lock
        f = None
        try:
            f = open(lock_file, "w")
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            try:
                with open(pending_file, "w") as pf:
                    pf.write("1")
            except Exception:
                pass
            if self._verbose:
                print(f"[VERBOSE] Reload for {name} is already running in another process. Queued.")
            t_lock.release()
            if f:
                f.close()
            return
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

    def reload_all(self) -> list[threading.Thread]:
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
