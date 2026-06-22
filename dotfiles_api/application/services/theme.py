from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.domain.contracts.theme_store import ThemeStore
from dotfiles_api.domain.events import EventBus, ThemeChangedEvent

class ThemeService:
    def __init__(self, loader: ThemeLoader, store: ThemeStore, event_bus: EventBus) -> None:
        self._loader = loader
        self._store = store
        self._event_bus = event_bus

    def apply_theme(self, theme_name: str) -> None:
        tokens = self._loader.load(theme_name)
        self._store.set_active_theme(theme_name)
        self._event_bus.publish(ThemeChangedEvent(theme_name=theme_name, tokens=tokens))
