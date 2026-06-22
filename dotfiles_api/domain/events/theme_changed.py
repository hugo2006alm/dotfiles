from dataclasses import dataclass
from dotfiles_api.domain.tokens.design_tokens import DesignTokens

@dataclass(frozen=True)
class ThemeChangedEvent:
    theme_name: str
    tokens: DesignTokens
