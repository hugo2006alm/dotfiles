from dataclasses import dataclass
from dotfiles_api.domain.tokens.color_tokens import ColorTokens
from dotfiles_api.domain.tokens.metric_tokens import MetricTokens
from dotfiles_api.domain.tokens.typography_tokens import TypographyTokens

@dataclass(frozen=True)
class DesignTokens:
    colors: ColorTokens
    metrics: MetricTokens
    typography: TypographyTokens
