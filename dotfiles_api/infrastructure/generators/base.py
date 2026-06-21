from abc import ABC, abstractmethod
from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.domain.events import EventBus, ThemeChangedEvent, ConfigGeneratedEvent
from dotfiles_api.application.transaction import ConfigTransaction

class BaseGenerator(ABC):
    def __init__(self, name: str, transaction: ConfigTransaction, event_bus: EventBus) -> None:
        self.name = name
        self.transaction = transaction
        self.event_bus = event_bus

    def handle_theme_changed(self, event: ThemeChangedEvent) -> None:
        self.generate(event.tokens)

    def generate(self, tokens: DesignTokens) -> None:
        with self.transaction as tx:
            artifacts = self.render(tokens)
            for artifact in artifacts:
                tx.write_artifact(artifact)
        
        self.event_bus.publish(ConfigGeneratedEvent(generator_name=self.name))

    @abstractmethod
    def render(self, tokens: DesignTokens) -> list[GeneratedArtifact]:
        ...
