import re
from pathlib import Path
from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class WalkerGenerator(BaseGenerator):
    def __init__(self, name: str = "walker", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        bg = tokens.colors.colors.get("background", "#F4EFE4")
        bg2 = tokens.colors.colors.get("background2", "#EDE7D3")
        fg = tokens.colors.colors.get("foreground", "#0D0D0D")
        fg2 = tokens.colors.colors.get("foreground2", "#3A3A3A")
        border = tokens.colors.colors.get("border", "#0D0D0D")
        accent = tokens.colors.colors.get("accent", "#D94F2B")
        inactive = tokens.colors.colors.get("inactive", "#C8C2B4")
        font_mono = tokens.typography.typography.get("font_mono", "SpaceMono")
        font_size_sm = tokens.typography.typography.get("font_size_sm", "11")
        font_size_md = tokens.typography.typography.get("font_size_md", "13")

        colors_content = f"""// Auto-generated from themes/{theme_name}/colors.toml — do not edit directly
$background:   {bg};
$background2:  {bg2};
$foreground:   {fg};
$foreground2:  {fg2};
$border:       {border};
$accent:       {accent};
$inactive:     {inactive};
$font_mono:    "{font_mono}";
$font_size_sm: {font_size_sm}px;
$font_size_md: {font_size_md}px;
"""

        conf_source = Path("/etc/xdg/walker/config.toml")
        if conf_source.exists():
            try:
                orig = conf_source.read_text()
                config_content = re.sub(r'^theme\s*=.*', f'theme = "{theme_name}"', orig, flags=re.MULTILINE)
                config_content = re.sub(r'\[\[providers\.prefixes\]\]\nprefix\s*=\s*"="\nprovider\s*=\s*"calc"', '', config_content)
                if '"default" = {' in config_content:
                    placeholder_insert = '"default" = { input = "Search", list = "No Results" }\n"calc" = { input = "Calculator", list = "Enter math equation..." }\n"symbols" = { input = "Symbols", list = "No symbols found" }'
                    config_content = config_content.replace('"default" = { input = "Search", list = "No Results" }', placeholder_insert)
                if "[providers.symbols]" not in config_content:
                    config_content += "\n[providers.symbols]\nshow_initial_entries = true\n"
            except Exception:
                config_content = self._get_fallback_config(theme_name)
        else:
            config_content = self._get_fallback_config(theme_name)

        return [
            GeneratedArtifact(artifact_id="walker-colors", content=colors_content),
            GeneratedArtifact(artifact_id="walker-config", content=config_content)
        ]

    def _get_fallback_config(self, theme_name: str) -> str:
        return f"""theme = "{theme_name}"

[search]
placeholder = "Search..."

[placeholders]
"default" = {{ input = "Search", list = "No Results" }}
"calc" = {{ input = "Calculator", list = "Enter math equation..." }}
"symbols" = {{ input = "Symbols", list = "No symbols found" }}

[providers]
default = ["desktopapplications", "calc", "websearch"]
empty = ["desktopapplications"]

[[providers.prefixes]]
prefix = "."
provider = "symbols"
"""
