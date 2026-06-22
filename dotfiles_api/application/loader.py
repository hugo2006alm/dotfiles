import tomllib
from pathlib import Path
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.domain.tokens.color_tokens import ColorTokens
from dotfiles_api.domain.tokens.metric_tokens import MetricTokens
from dotfiles_api.domain.tokens.typography_tokens import TypographyTokens
from dotfiles_api.domain.tokens.design_tokens import DesignTokens

class ThemeLoader:
    def __init__(self, env: EnvironmentContext) -> None:
        self._env = env

    def load(self, theme_name: str) -> DesignTokens:
        theme_path = self._env.home_dir / ".config" / "themes" / theme_name / "colors.toml"
        if not theme_path.exists():
            raise FileNotFoundError(f"Theme file '{theme_path}' does not exist.")
            
        with open(theme_path, "rb") as f:
            colors_data = tomllib.load(f)
            
        style_path = self._env.home_dir / ".config" / "themes" / "style.toml"
        metrics_data = {}
        typography_data = {}
        
        if style_path.exists():
            with open(style_path, "rb") as f:
                style_data = tomllib.load(f)
            for k, v in style_data.items():
                if k.startswith("font_"):
                    typography_data[k] = v
                else:
                    metrics_data[k] = v
        
        return DesignTokens(
            colors=ColorTokens(colors=colors_data),
            metrics=MetricTokens(metrics=metrics_data),
            typography=TypographyTokens(typography=typography_data)
        )
