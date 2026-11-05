from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.domain.contracts.theme_store import ThemeStore
from dotfiles_api.domain.events import EventBus, ThemeChangedEvent
from dotfiles_api.application.planner import ThemePlanner

class ThemeService:
    def __init__(self, loader: ThemeLoader, store: ThemeStore, event_bus: EventBus,
                 planner: ThemePlanner | None = None, dry_run: bool = False) -> None:
        self._loader = loader
        self._store = store
        self._event_bus = event_bus
        self._planner = planner
        self._dry_run = dry_run

    def get_active_theme(self) -> str:
        return self._store.get_active_theme()

    def apply_theme(self, theme_name: str):
        tokens = self._loader.load(theme_name)
        plan = self._planner.build(tokens, theme_name) if self._planner else None
        if plan is not None:
            plan.describe()
        if self._dry_run:
            print("No changes applied.")
            return plan
        self._store.set_active_theme(theme_name)
        self._event_bus.publish(ThemeChangedEvent(theme_name=theme_name, tokens=tokens))
        return plan
