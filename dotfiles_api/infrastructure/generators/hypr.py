from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class HyprlandGenerator(BaseGenerator):
    def __init__(self, name: str = "hyprland", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens) -> list[GeneratedArtifact]:
        colors_lines = []
        for k, v in sorted(tokens.colors.colors.items()):
            colors_lines.append(f"    {k} = '{v}',")
        colors_content = "return {\n" + "\n".join(colors_lines) + "\n}\n"

        metrics_lines = []
        for k, v in sorted(tokens.metrics.metrics.items()):
            if isinstance(v, str):
                metrics_lines.append(f"    {k} = '{v}',")
            elif isinstance(v, bool):
                metrics_lines.append(f"    {k} = {str(v).lower()},")
            else:
                metrics_lines.append(f"    {k} = {v},")
        metrics_content = "return {\n" + "\n".join(metrics_lines) + "\n}\n"

        return [
            GeneratedArtifact(artifact_id="hyprland-colors", content=colors_content),
            GeneratedArtifact(artifact_id="hyprland-style", content=metrics_content)
        ]
