from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class VesktopGenerator(BaseGenerator):
    def __init__(self, name: str = "vesktop", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        bg = tokens.colors.colors.get("background", "#F4EFE4")
        bg2 = tokens.colors.colors.get("background2", "#EDE7D3")
        fg = tokens.colors.colors.get("foreground", "#0D0D0D")
        fg2 = tokens.colors.colors.get("foreground2", "#3A3A3A")
        accent = tokens.colors.colors.get("accent", "#D94F2B")
        accent_fg = tokens.colors.colors.get("accent_fg", "#F4EFE4")
        inactive = tokens.colors.colors.get("inactive", "#C8C2B4")
        urgent = tokens.colors.colors.get("urgent", "#D94F2B")
        selection = tokens.colors.colors.get("selection", "#0D0D0D")

        content = f"""/**
 * @name {theme_name}
 * @author Generator
 * @version 1.0.0
 * @description Ink on paper theme
 */
.theme-dark, .theme-light, :root {{
  --background-primary: {bg};
  --background-secondary: {bg2};
  --background-secondary-alt: {inactive};
  --background-tertiary: {bg2};
  --background-floating: {bg};
  --background-nested-floating: {bg2};
  --background-message-hover: rgba(0, 0, 0, 0.05);
  --channeltextarea-background: {bg2};
  --info-positive-background: {bg2};
  --info-warning-background: {bg2};
  --info-danger-background: {bg2};

  --text-normal: {fg};
  --text-muted: {fg2};
  --text-link: {accent};
  --header-primary: {fg};
  --header-secondary: {fg2};
  --interactive-normal: {fg};
  --interactive-hover: {accent};
  --interactive-active: {accent_fg};
  --interactive-muted: {inactive};

  --brand-experiment: {accent};
  --brand-experiment-500: {accent};
  --brand-experiment-560: {accent};
  --brand-experiment-600: {accent};

  --button-danger-background: {urgent};

  --background-modifier-selected: {selection};
  --background-modifier-hover: rgba(127, 127, 127, 0.1);
  --background-modifier-active: rgba(127, 127, 127, 0.2);
  --background-modifier-accent: rgba(127, 127, 127, 0.1);

  --scrollbar-auto-thumb: {fg};
  --scrollbar-auto-track: transparent;
  --scrollbar-thin-thumb: {fg};
  --scrollbar-thin-track: transparent;

  --border-radius: 0px;
}}
* {{
    border-radius: 0 !important;
    box-shadow: none !important;
}}
::-webkit-scrollbar {{
    width: 8px !important;
}}
::-webkit-scrollbar-thumb {{
    background: var(--scrollbar-auto-thumb) !important;
    border-radius: 0 !important;
}}
"""
        return [
            GeneratedArtifact(artifact_id="vesktop-theme", content=content)
        ]
