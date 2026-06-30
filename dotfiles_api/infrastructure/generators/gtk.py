import subprocess
import shutil
from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class GtkGenerator(BaseGenerator):
    def __init__(self, name: str = "gtk", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
        super().__init__(name, transaction, event_bus)

    def render(self, tokens: DesignTokens, theme_name: str) -> list[GeneratedArtifact]:
        is_dark = "dark" in theme_name
        if is_dark:
            gtk_theme = "Adwaita-dark"
            icon_theme = "Papirus-Dark"
        else:
            gtk_theme = "Adwaita"
            icon_theme = "Papirus-Light"

        cursor_theme = tokens.metrics.metrics.get("cursor_theme", "Bibata-Modern-Classic")
        cursor_size = tokens.metrics.metrics.get("cursor_size", "24")
        font_mono = tokens.typography.typography.get("font_mono", "Monaspace Radon")
        font_size_md = tokens.typography.typography.get("font_size_md", "13")

        settings_ini = f"""[Settings]
gtk-theme-name = {gtk_theme}
gtk-icon-theme-name = {icon_theme}
gtk-font-name = {font_mono} {font_size_md}
gtk-cursor-theme-name = {cursor_theme}
gtk-cursor-theme-size = {cursor_size}
"""

        background = tokens.colors.colors.get("background", "#F4EFE4")
        background2 = tokens.colors.colors.get("background2", "#EDE7D3")
        foreground = tokens.colors.colors.get("foreground", "#0D0D0D")
        accent = tokens.colors.colors.get("accent", "#D94F2B")
        accent_fg = tokens.colors.colors.get("accent_fg", "#F4EFE4")
        accent_hover = tokens.colors.colors.get("color9", "#E8623E")

        gtk_css = f"""/* Auto-generated from themes/{theme_name}/colors.toml — do not edit directly */

/* Custom GTK styling for Nautilus & system apps */
window.background.csd,
window.background.csd > decoration {{
  border-radius: 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
}}

.nautilus-window {{
  background-color: {background};
  color: {foreground};
}}

.nautilus-window .sidebar {{
  background-color: {background2};
  border-right: 1px solid {background};
}}

.nautilus-window .sidebar row:selected {{
  background-color: {accent};
  color: {accent_fg};
  border-radius: 6px;
}}

.nautilus-window .view,
.nautilus-window .view row {{
  background-color: {background};
  color: {foreground};
}}

.nautilus-window .view row:selected {{
  background-color: {accent};
  color: {accent_fg};
}}

button.suggested-action {{
  background-color: {accent};
  color: {accent_fg};
}}

button.suggested-action:hover {{
  background-color: {accent_hover};
}}
"""

        folder_color = tokens.colors.colors.get("papirus_folder_color")
        if not folder_color:
            accent_val = tokens.colors.colors.get("accent", "")
            if accent_val in ["#D94F2B", "#E8623E", "#B33E20"]:
                folder_color = "orange"
            elif accent_val in ["#6B8E23", "#556B2F"]:
                folder_color = "green"
            else:
                folder_color = "grey"

        if shutil.which("papirus-folders"):
            try:
                subprocess.Popen(["papirus-folders", "-C", folder_color], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        return [
            GeneratedArtifact(artifact_id="gtk3-settings", content=settings_ini),
            GeneratedArtifact(artifact_id="gtk4-settings", content=settings_ini),
            GeneratedArtifact(artifact_id="gtk3-css", content=gtk_css),
            GeneratedArtifact(artifact_id="gtk4-css", content=gtk_css)
        ]
