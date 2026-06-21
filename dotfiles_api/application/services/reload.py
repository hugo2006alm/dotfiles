from dotfiles_api.domain.contracts.reloadable import Reloadable
from dotfiles_api.domain.events import ConfigGeneratedEvent, ReloadRequestedEvent

class ReloadService:
    def __init__(self, reloadables: list[Reloadable]) -> None:
        self._reloadables = reloadables

    def reload_all(self) -> None:
        for reloadable in self._reloadables:
            reloadable.reload()

    def handle_config_generated(self, event: ConfigGeneratedEvent) -> None:
        self.reload_all()

    def handle_reload_requested(self, event: ReloadRequestedEvent) -> None:
        self.reload_all()
