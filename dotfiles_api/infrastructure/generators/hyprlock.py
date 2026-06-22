from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class HyprlockGenerator(BaseGenerator):
    def __init__(self, name: str = "hyprlock", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        lock_bg = tokens.colors.colors.get("background", "#000000").lstrip("#")
        lock_fg = tokens.colors.colors.get("foreground", "#FFFFFF").lstrip("#")
        lock_input = tokens.colors.colors.get("foreground", "#FFFFFF").lstrip("#")
        accent = tokens.colors.colors.get("accent", "#FF0000").lstrip("#")

        content = f"""# Auto-generated from themes/{theme_name}/colors.toml — do not edit directly

background {{
    monitor =
    color = rgb({lock_bg})
    blur_passes = 0
}}

label {{
    monitor =
    text = $TIME
    color = rgb({lock_fg})
    font_size = 128
    font_family = Bebas Neue
    position = 0, 160
    halign = center
    valign = center
}}

label {{
    monitor =
    text = cmd[update:60000] date +'%A, %d %B %Y' | tr '[:lower:]' '[:upper:]'
    color = rgb({lock_fg})
    font_size = 14
    font_family = JetBrains Mono Nerd Font
    position = 0, 60
    halign = center
    valign = center
}}

label {{
    monitor =
    text = // LOCKED
    color = rgb({accent})
    font_size = 11
    font_family = JetBrains Mono Nerd Font
    position = 0, -40
    halign = center
    valign = center
}}

input-field {{
    monitor =
    size = 320, 50
    outline_thickness = 3
    dots_size = 0.25
    dots_spacing = 0.35
    dots_center = false
    outer_color = rgb({lock_input})
    inner_color = rgb({lock_bg})
    font_color = rgb({lock_fg})
    fade_on_empty = true
    placeholder_text = <span font_family="JetBrains Mono Nerd Font" font_size="13">PASSWORD</span>
    rounding = 0
    position = 0, -110
    halign = center
    valign = center
}}
"""
        return [
            GeneratedArtifact(artifact_id="hyprlock-config", content=content)
        ]
