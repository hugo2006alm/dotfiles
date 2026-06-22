from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class GhosttyGenerator(BaseGenerator):
    def __init__(self, name: str = "ghostty", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        bg = tokens.colors.colors.get("background", "#F4EFE4").lstrip("#")
        fg = tokens.colors.colors.get("foreground", "#0D0D0D").lstrip("#")
        font_mono = tokens.typography.typography.get("font_mono", "Monaspace Radon")
        font_size = tokens.typography.typography.get("font_size_md", "13")

        content = f"""# Auto-generated — do not edit directly
background = {bg}
foreground = {fg}
font-family = {font_mono}
font-size = {font_size}
"""
        return [
            GeneratedArtifact(artifact_id="ghostty-colors", content=content)
        ]
