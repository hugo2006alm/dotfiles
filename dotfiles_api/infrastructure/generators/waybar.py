from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class WaybarGenerator(BaseGenerator):
    def __init__(self, name: str = "waybar", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        scss_lines = []
        for k, v in sorted(tokens.colors.colors.items()):
            scss_lines.append(f"${k}: {v};")
        scss_content = "\n".join(scss_lines) + "\n"
        
        return [
            GeneratedArtifact(artifact_id="waybar-colors", content=scss_content)
        ]
