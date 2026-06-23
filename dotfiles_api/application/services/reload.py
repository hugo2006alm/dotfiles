import threading
from dotfiles_api.domain.contracts.reloadable import Reloadable, EventReloadable
from dotfiles_api.domain.events import ConfigGeneratedEvent, ReloadRequestedEvent

class ReloadService:
    def __init__(self, reloadables: list[Reloadable], verbose: bool = False) -> None:
        self._reloadables = reloadables
        self._verbose = verbose
        self._event_reloadables = [
            r for r in reloadables if isinstance(r, EventReloadable)
        ]

    def reload_all(self) -> list[threading.Thread]:
        if self._verbose:
            print(f"[VERBOSE] Reloading all {len(self._reloadables)} reloadables in parallel threads")
        threads = []
        for reloadable in self._reloadables:
            if self._verbose:
                print(f"[VERBOSE] Spawning reload thread for: {reloadable.__class__.__name__}")
            t = threading.Thread(target=reloadable.reload)
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
                t = threading.Thread(target=r.reload)
                t.start()
                threads.append(t)
        return threads

    def handle_reload_requested(self, event: ReloadRequestedEvent) -> None:
        self.reload_all()

