from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class WlogoutGenerator(BaseGenerator):
    def __init__(self, name: str = "wlogout", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        bg = tokens.colors.colors.get("background", "#16130F")
        bg2 = tokens.colors.colors.get("background2", "#201C17")
        fg = tokens.colors.colors.get("foreground", "#F4EFE4")
        accent = tokens.colors.colors.get("accent", "#E8623E")
        accent_fg = tokens.colors.colors.get("accent_fg", "#16130F")
        shadow = tokens.colors.colors.get("shadow", "#000000")

        content = f"""// Auto-generated from themes/{theme_name}/colors.toml — do not edit directly
$background: {bg};
$background2: {bg2};
$foreground: {fg};
$accent: {accent};
$accent_fg: {accent_fg};
$shadow: {shadow};
"""
        return [
            GeneratedArtifact(artifact_id="wlogout-colors", content=content)
        ]
