from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class SwayosdGenerator(BaseGenerator):
    def __init__(self, name: str = "swayosd", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        bg = tokens.colors.colors.get("background", "#F4EFE4")
        fg = tokens.colors.colors.get("foreground", "#0D0D0D")
        accent = tokens.colors.colors.get("accent", "#D94F2B")
        inactive = tokens.colors.colors.get("inactive", "#C8C2B4")
        shadow = tokens.colors.colors.get("shadow", "#0D0D0D")

        content = f"""// Auto-generated from themes/{theme_name}/colors.toml — do not edit directly
$background: {bg};
$foreground: {fg};
$accent:     {accent};
$inactive:   {inactive};
$shadow:     {shadow};
"""
        return [
            GeneratedArtifact(artifact_id="swayosd-colors", content=content)
        ]
