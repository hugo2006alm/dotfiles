from pathlib import Path
from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class GreetdGenerator(BaseGenerator):
    def __init__(self, name: str = "greetd", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        is_dark = "dark" in theme_name
        is_dark_str = "true" if is_dark else "false"
        bg_file = "/etc/greetd/regreet-background.jpg"

        content = f"""[background]
path = "{bg_file}"
fit = "Cover"

[GTK]
application_prefer_dark_theme = {is_dark_str}
"""

        return [
            GeneratedArtifact(artifact_id="greetd-config", content=content)
        ]
