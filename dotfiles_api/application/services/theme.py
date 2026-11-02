from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.domain.contracts.theme_store import ThemeStore
from dotfiles_api.domain.events import EventBus, ThemeChangedEvent
from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.theme_coordinator import ThemeCoordinator

class ThemeService:
    def __init__(self, loader: ThemeLoader, store: ThemeStore, event_bus: EventBus,
                 planner: ThemePlanner | None = None, dry_run: bool = False,
                 coordinator: ThemeCoordinator | None = None, on_applied=None) -> None:
        self._loader = loader
        self._store = store
        self._event_bus = event_bus
        self._planner = planner
        self._dry_run = dry_run
        self._coordinator = coordinator
        self._on_applied = on_applied

    def apply_theme(self, theme_name: str):
        tokens = self._loader.load(theme_name)
        if self._coordinator is not None:
            plan = self._coordinator.apply(tokens, theme_name, dry_run=self._dry_run)
            if not self._dry_run:
                self._event_bus.publish(ThemeChangedEvent(theme_name=theme_name, tokens=tokens))
                if self._on_applied is not None:
                    self._on_applied(plan.changed_generators)
            return plan
        plan = self._planner.build(tokens, theme_name) if self._planner else None
        if plan is not None:
            plan.describe()
        if self._dry_run:
            print("No changes applied.")
            return plan
        self._store.set_active_theme(theme_name)
        self._event_bus.publish(ThemeChangedEvent(theme_name=theme_name, tokens=tokens))
        return plan

    def rollback(self):
        if self._coordinator is None:
            raise ValueError("Theme rollback requires the transaction coordinator.")
        generators = self._coordinator.rollback(dry_run=self._dry_run)
        if not self._dry_run and self._on_applied is not None:
            self._on_applied(generators)
        return generators
