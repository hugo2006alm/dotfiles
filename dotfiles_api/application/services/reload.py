from dotfiles_api.domain.contracts.reloadable import Reloadable, EventReloadable
from dotfiles_api.domain.events import ConfigGeneratedEvent, ReloadRequestedEvent

class ReloadService:
    def __init__(self, reloadables: list[Reloadable]) -> None:
        self._reloadables = reloadables
        self._event_reloadables = [
            r for r in reloadables if isinstance(r, EventReloadable)
        ]

    def reload_all(self) -> None:
        for reloadable in self._reloadables:
            reloadable.reload()

    def handle_config_generated(self, event: ConfigGeneratedEvent) -> None:
        for r in self._event_reloadables:
            if r.supports(event.generator_name):
                r.reload()

    def handle_reload_requested(self, event: ReloadRequestedEvent) -> None:
        self.reload_all()
