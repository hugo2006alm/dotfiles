from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class HyprlandGenerator(BaseGenerator):
    def __init__(self, name: str = "hyprland", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        def clean_hex(val: str) -> str:
            return val.lstrip("#")

        def to_lua_hex(val: str) -> str:
            return f"0x{clean_hex(val).upper()}"

        bg = tokens.colors.colors.get("background", "#F4EFE4")
        bg2 = tokens.colors.colors.get("background2", "#EDE7D3")
        fg = tokens.colors.colors.get("foreground", "#0D0D0D")
        fg2 = tokens.colors.colors.get("foreground2", "#3A3A3A")
        border = tokens.colors.colors.get("border", "#0D0D0D")
        accent = tokens.colors.colors.get("accent", "#D94F2B")
        accent2 = tokens.colors.colors.get("accent2", "#B33E20")
        active = tokens.colors.colors.get("active", "#0D0D0D")
        inactive = tokens.colors.colors.get("inactive", "#C8C2B4")
        urgent = tokens.colors.colors.get("urgent", "#D94F2B")
        shadow = tokens.colors.colors.get("shadow", "#0D0D0D")
        
        try:
            shadow_alpha = float(tokens.colors.colors.get("shadow_alpha", "0.4"))
        except ValueError:
            shadow_alpha = 0.4

        shadow_alpha_hex = f"{int(shadow_alpha * 255):02X}"
        shadow_rgba = f"{clean_hex(shadow)}{shadow_alpha_hex}"

        colors_conf = f"""# Auto-generated from themes/{theme_name}/colors.toml — do not edit directly
$background  = rgb({clean_hex(bg)})
$background2 = rgb({clean_hex(bg2)})
$foreground  = rgb({clean_hex(fg)})
$foreground2 = rgb({clean_hex(fg2)})
$border      = rgb({clean_hex(border)})
$accent      = rgb({clean_hex(accent)})
$accent2     = rgb({clean_hex(accent2)})
$active      = rgb({clean_hex(active)})
$inactive    = rgb({clean_hex(inactive)})
$urgent      = rgb({clean_hex(urgent)})
$shadow      = rgba({shadow_rgba})
"""

        colors_lua = f"""-- Auto-generated from themes/{theme_name}/colors.toml — do not edit directly
return {{
    background    = {to_lua_hex(bg)},
    background2   = {to_lua_hex(bg2)},
    foreground    = {to_lua_hex(fg)},
    foreground2   = {to_lua_hex(fg2)},
    border        = {to_lua_hex(border)},
    accent        = {to_lua_hex(accent)},
    accent2       = {to_lua_hex(accent2)},
    active        = {to_lua_hex(active)},
    inactive      = {to_lua_hex(inactive)},
    urgent        = {to_lua_hex(urgent)},
    shadow        = 0x{shadow_rgba.upper()},
}}
"""

        border_size = tokens.metrics.metrics.get("border_size", "3")
        gaps_inner = tokens.metrics.metrics.get("gaps_inner", "4")
        gaps_outer = tokens.metrics.metrics.get("gaps_outer", "8")
        corner_radius = tokens.metrics.metrics.get("corner_radius", "0")
        cursor_theme = tokens.metrics.metrics.get("cursor_theme", "Bibata-Modern-Classic")
        cursor_size = tokens.metrics.metrics.get("cursor_size", "24")
        font_mono = tokens.typography.typography.get("font_mono", "Monaspace Radon")
        font_display = tokens.typography.typography.get("font_display", "Bebas Neue")
        font_size_sm = tokens.typography.typography.get("font_size_sm", "11")
        font_size_md = tokens.typography.typography.get("font_size_md", "13")
        font_size_lg = tokens.typography.typography.get("font_size_lg", "24")
        shadow_offset_x = tokens.metrics.metrics.get("shadow_offset_x", "2")
        shadow_offset_y = tokens.metrics.metrics.get("shadow_offset_y", "2")
        shadow_range = tokens.metrics.metrics.get("shadow_range", "4")
        shadow_render_power = tokens.metrics.metrics.get("shadow_render_power", "4")

        style_conf = f"""# Auto-generated from themes/style.toml — do not edit directly
$border_size         = {border_size}
$gaps_inner          = {gaps_inner}
$gaps_outer          = {gaps_outer}
$corner_radius       = {corner_radius}
$cursor_theme        = {cursor_theme}
$cursor_size         = {cursor_size}
$font_mono           = {font_mono}
$font_display        = {font_display}
$font_size_sm        = {font_size_sm}
$font_size_md        = {font_size_md}
$font_size_lg        = {font_size_lg}
$shadow_offset_x     = {shadow_offset_x}
$shadow_offset_y     = {shadow_offset_y}
$shadow_range        = {shadow_range}
$shadow_render_power = {shadow_render_power}
"""

        style_lua = f"""-- Auto-generated from themes/style.toml — do not edit directly
return {{
    border_size         = {border_size},
    gaps_inner          = {gaps_inner},
    gaps_outer          = {gaps_outer},
    corner_radius       = {corner_radius},
    cursor_theme        = "{cursor_theme}",
    cursor_size         = {cursor_size},
    font_mono           = "{font_mono}",
    font_display        = "{font_display}",
    font_size_sm        = {font_size_sm},
    font_size_md        = {font_size_md},
    font_size_lg        = {font_size_lg},
    shadow_offset_x     = {shadow_offset_x},
    shadow_offset_y     = {shadow_offset_y},
    shadow_range        = {shadow_range},
    shadow_render_power = {shadow_render_power},
}}
"""

        return [
            GeneratedArtifact(artifact_id="hyprland-colors", content=colors_lua),
            GeneratedArtifact(artifact_id="hyprland-colors-conf", content=colors_conf),
            GeneratedArtifact(artifact_id="hyprland-style", content=style_lua),
            GeneratedArtifact(artifact_id="hyprland-style-conf", content=style_conf),
        ]
