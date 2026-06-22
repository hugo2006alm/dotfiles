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
        
        vars_lines = []
        font_mono = tokens.typography.typography.get("font_mono", "monospace")
        font_display = tokens.typography.typography.get("font_display", "sans-serif")
        border_size = tokens.metrics.metrics.get("border_size", "2")
        corner_radius = tokens.metrics.metrics.get("corner_radius", "0")
        
        vars_lines.append(f"$font-mono: '{font_mono}';")
        vars_lines.append(f"$font-display: '{font_display}';")
        vars_lines.append(f"$border-size: {border_size}px;")
        vars_lines.append(f"$corner-radius: {corner_radius}px;")
        
        for k, v in sorted(tokens.typography.typography.items()):
            scss_k = k.replace("_", "-")
            if scss_k not in ["font-mono", "font-display"]:
                vars_lines.append(f"${scss_k}: {v};")
        for k, v in sorted(tokens.metrics.metrics.items()):
            scss_k = k.replace("_", "-")
            if scss_k not in ["border-size", "corner-radius"]:
                vars_lines.append(f"${scss_k}: {v};")
                
        vars_content = "\n".join(vars_lines) + "\n"
        
        return [
            GeneratedArtifact(artifact_id="waybar-colors", content=scss_content),
            GeneratedArtifact(artifact_id="waybar-variables", content=vars_content)
        ]
