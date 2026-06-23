import json
import tomllib
from pathlib import Path
from dotfiles_api.domain.tokens import DesignTokens
from dotfiles_api.domain.artifacts import GeneratedArtifact
from dotfiles_api.infrastructure.generators.base import BaseGenerator
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.domain.events import EventBus

class SwayncGenerator(BaseGenerator):
    def __init__(self, name: str = "swaync", transaction: ConfigTransaction = None, event_bus: EventBus = None) -> None:
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

        # 1. Scan themes directory
        theme_dir = Path.home() / ".config" / "themes"
        themes = []
        if theme_dir.is_dir():
            for p in theme_dir.iterdir():
                if p.is_dir() and (p / "colors.toml").is_file():
                    themes.append(p.name)
        themes.sort()

        # If empty (e.g. in test env), default to theme_name
        if not themes:
            themes = [theme_name]

        # 2. Load theme colors
        theme_colors = {}
        for t in themes:
            toml_path = theme_dir / t / "colors.toml"
            if toml_path.is_file():
                try:
                    with open(toml_path, "rb") as f:
                        data = tomllib.load(f)
                    colors = data.get("colors", data)
                    theme_colors[t] = {
                        "bg": colors.get("background", "#F4EFE4"),
                        "accent": colors.get("accent", "#D94F2B"),
                        "fg": colors.get("foreground", "#0D0D0D")
                    }
                except Exception:
                    theme_colors[t] = {"bg": "#F4EFE4", "accent": "#D94F2B", "fg": "#0D0D0D"}
            else:
                # Fallback to current token values if not found (mainly for testing)
                theme_colors[t] = {"bg": bg, "accent": accent, "fg": fg}

        # 3. Generate config.json (swaync-config)
        config_data = {
            "$schema": "/etc/xdg/swaync/configSchema.json",
            "notification-visibility": {
                "spotify": {"state": "ignored", "app-name": "Spotify"},
                "zen": {"state": "ignored", "app-name": "Zen Browser"},
                "zen-app": {"state": "ignored", "app-name": "zen"},
                "chrome": {"state": "ignored", "app-name": "Google Chrome"},
                "firefox": {"state": "ignored", "app-name": "Firefox"}
            },
            "positionX": "right",
            "positionY": "top",
            "control-center-width": 380,
            "control-center-height": 860,
            "control-center-margin-top": 10,
            "control-center-margin-bottom": 10,
            "control-center-margin-right": 10,
            "control-center-margin-left": 10,
            "notification-window-width": 400,
            "layer": "top",
            "cssPriority": "application",
            "notification-icon-size": 64,
            "notification-body-image-height": 100,
            "notification-body-image-width": 200,
            "timeout": 10,
            "timeout-low": 5,
            "timeout-critical": 0,
            "fit-to-screen": True,
            "keyboard-shortcuts": True,
            "image-visibility": "always",
            "transition-time": 200,
            "hide-on-clear": False,
            "hide-on-action": True,
            "widgets": [
                "title",
                "dnd",
                "mpris",
                "volume",
                "buttons-grid#updates",
                "buttons-grid#themes",
                "label#wallpaper",
                "notifications"
            ],
            "widget-config": {
                "title": {
                    "text": "Notifications",
                    "clear-all-button": True,
                    "button-text": "Clear All"
                },
                "dnd": {
                    "text": "Do Not Disturb"
                },
                "mpris": {
                    "image-size": 96,
                    "image-radius": 4
                },
                "volume": {
                    "label": "󰕾"
                },
                "buttons-grid#updates": {
                    "buttons-per-row": 1,
                    "actions": [
                        {
                            "label": "Check for Updates",
                            "command": f"sh -c 'ghostty --class=com.system.update --title=\"System Update\" -e {Path.home()}/.config/waybar/scripts/system-update.sh'"
                        }
                    ]
                },
                "buttons-grid#themes": {
                    "buttons-per-row": 4,
                    "actions": [
                        {
                            "label": t,
                            "command": f"dotfiles configure --theme {t}"
                        } for t in themes
                    ]
                },
                "label#wallpaper": {
                    "text": " ",
                    "clear-all-button": False
                }
            }
        }

        # 4. Generate style.css (swaync-style)
        style_content = f"""/* Auto-generated from themes/{theme_name}/colors.toml — do not edit directly */

* {{
  font-family: "{font_mono}", monospace;
  box-shadow: none;
}}

/* ── Control Center ── */
.control-center {{
  background: {bg};
  border: 3px solid {border};
  border-radius: 0px;
  color: {fg};
  padding: 16px;
}}

/* ── Title Widget ── */
.widget-title {{
  margin: 8px 0;
}}
.widget-title > label {{
  font-size: 16px;
  font-weight: bold;
  color: {fg};
}}
.widget-title > button {{
  background: {bg2};
  border: 2px solid {border};
  border-radius: 0px;
  color: {fg};
  padding: 6px 12px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
}}
.widget-title > button:hover {{
  background: {accent};
  color: {bg};
  border-color: {accent};
}}

/* ── DND Widget ── */
.widget-dnd {{
  margin: 8px 0;
  font-size: 13px;
  color: {fg};
}}
.widget-dnd > switch {{
  background: {bg2};
  border: 2px solid {border};
  border-radius: 0px;
}}
.widget-dnd > switch:checked {{
  background: {accent};
  border-color: {accent};
}}
.widget-dnd > switch slider {{
  background: {fg};
  border-radius: 0px;
}}

/* ── MPRIS Widget ── */
.widget-mpris {{
  background: {bg2};
  border: 2px solid {border};
  border-radius: 0px;
  padding: 12px;
  margin: 8px 0;
}}
.widget-mpris-player {{
  padding: 4px;
}}
.widget-mpris-title {{
  font-weight: bold;
  font-size: 13px;
}}
.widget-mpris-subtitle {{
  font-size: 11px;
  color: {fg2};
}}

/* ── Sliders (Volume) ── */
.widget-volume {{
  background: {bg2};
  border: 2px solid {border};
  border-radius: 0px;
  padding: 8px 12px;
  margin: 6px 0;
}}
.widget-volume scale trough {{
  background: {inactive};
  border-radius: 0px;
  min-height: 8px;
}}
.widget-volume scale highlight {{
  background: {accent};
  border-radius: 0px;
}}

/* ── Updates Buttons Grid ── */
#updates {{
  margin: 8px 0;
}}
#updates > flowbox > flowboxchild > button {{
  background: {bg2};
  border: 2px solid {border};
  border-radius: 0px;
  color: {fg};
  padding: 10px 16px;
  font-weight: bold;
  font-size: 11px;
  text-transform: uppercase;
  margin: 4px 0;
}}
#updates > flowbox > flowboxchild > button:hover {{
  background: {accent};
  color: {bg};
  border-color: {accent};
}}

/* ── Themes Buttons Grid ── */
#themes {{
  margin: 8px 0;
}}
#themes > flowbox > flowboxchild > button {{
  color: transparent;
  text-shadow: none;
  font-size: 0px;
  min-height: 36px;
  padding: 0;
  margin: 4px;
}}
"""

        # Generate styled theme preview rectangles
        for i, t in enumerate(themes):
            colors = theme_colors[t]
            t_bg = colors["bg"]
            t_accent = colors["accent"]
            t_fg = colors["fg"]
            child_idx = i + 1

            style_content += f"""
#themes > flowbox > flowboxchild:nth-child({child_idx}) > button {{
  background: linear-gradient(to bottom, {t_bg} 70%, {t_accent} 70%);
  border: 2px solid {t_fg};
  border-radius: 0px;
}}
"""
            if t == theme_name:
                style_content += f"""
#themes > flowbox > flowboxchild:nth-child({child_idx}) > button {{
  outline: 3px solid {accent};
  outline-offset: -3px;
}}
"""

        # 5. Read active wallpaper for styling
        cache_dir = Path.home() / ".cache" / "shade-raid"
        last_wp_file = cache_dir / "last_wallpaper"
        wallpaper_path = ""
        if last_wp_file.is_file():
            try:
                wallpaper_path = last_wp_file.read_text().strip()
            except Exception:
                pass

        if wallpaper_path:
            style_content += f"""
/* ── Wallpaper Widget ── */
#wallpaper, .widget-wallpaper, #widget-wallpaper {{
  background-image: url("{wallpaper_path}");
  background-size: cover;
  background-position: center;
  min-height: 150px;
  border: 2px solid {border};
  border-radius: 0px;
  margin: 8px 0;
}}
"""
        else:
            style_content += f"""
/* ── Wallpaper Widget (Fallback) ── */
#wallpaper, .widget-wallpaper, #widget-wallpaper {{
  background-color: {bg2};
  min-height: 150px;
  border: 2px solid {border};
  border-radius: 0px;
  margin: 8px 0;
}}
"""

        style_content += f"""
/* ── Notifications ── */
.notification {{
  background: {bg2};
  border: 2px solid {border};
  border-radius: 0px;
  margin: 8px 0;
  padding: 12px;
}}
.notification-row {{
  outline: none;
}}
.notification-row:hover {{
  background: transparent;
}}
.notification-content {{
  padding: 4px;
}}
.notification-title {{
  font-weight: bold;
  font-size: 13px;
  color: {fg};
}}
.notification-body {{
  font-size: 11px;
  color: {fg2};
}}
.notification-action {{
  background: {bg};
  border: 2px solid {border};
  border-radius: 0px;
  color: {fg};
  font-size: 11px;
  font-weight: bold;
}}
.notification-action:hover {{
  background: {accent};
  color: {bg};
}}
"""

        return [
            GeneratedArtifact(artifact_id="swaync-config", content=json.dumps(config_data, indent=2)),
            GeneratedArtifact(artifact_id="swaync-style", content=style_content)
        ]
