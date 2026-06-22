from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class ReGreetGenerator(BaseGenerator):
    def __init__(self, name: str = "regreet", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        accent = tokens.colors.colors.get("accent", "#FF0000")
        accent_fg = tokens.colors.colors.get("accent_fg", "#FFFFFF")

        is_dark = "dark" in theme_name
        if is_dark:
            card_bg = "rgba(13, 13, 13, 0.78)"
            card_fg = "#F4EFE4"
            card_fg2 = "#C8C2B4"
            shadow = "rgba(0,0,0,0.6)"
        else:
            card_bg = "rgba(244, 239, 228, 0.84)"
            card_fg = "#0D0D0D"
            card_fg2 = "#3A3A3A"
            shadow = "rgba(0,0,0,0.25)"

        content = f"""/* ── Shade Raid — ReGreet Login Theme ── */
/* Generated from: {theme_name} */

@keyframes card-appear {{
    from {{
        opacity: 0;
        transform: translateY(12px) scale(0.98);
        filter: blur(6px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0) scale(1);
        filter: blur(0px);
    }}
}}

@keyframes unblur-bg {{
    from {{ filter: blur(30px) brightness(0.6); }}
    to   {{ filter: blur(0px)  brightness(1.0); }}
}}

/* ── Root window ── */
window {{
    background-color: transparent;
    animation: unblur-bg 1.2s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}}

/* ── Login card ── */
.login-box {{
    background-color: {card_bg};
    border: 5px solid {accent};
    border-radius: 4px;
    padding: 40px 48px;
    min-width: 380px;
    box-shadow: 0 24px 64px {shadow}, 0 2px 8px {shadow};
    animation: card-appear 0.9s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}}

/* ── Typography ── */
* {{
    font-family: "SpaceMono Nerd Font", "Space Mono", monospace;
    color: {card_fg};
}}

label {{
    color: {card_fg};
    font-size: 13px;
    letter-spacing: 0.04em;
}}

label.subtitle,
label:not(.title) {{
    color: {card_fg2};
    font-size: 11px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
"""
        return [
            GeneratedArtifact(artifact_id="regreet-style", content=content)
        ]
