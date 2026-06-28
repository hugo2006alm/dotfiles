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
                        "bg2": colors.get("background2", "#EDE7D3"),
                        "fg": colors.get("foreground", "#0D0D0D"),
                        "accent": colors.get("accent", "#D94F2B"),
                        "inactive": colors.get("inactive", "#C8C2B4")
                    }
                except Exception:
                    theme_colors[t] = {
                        "bg": "#F4EFE4",
                        "bg2": "#EDE7D3",
                        "fg": "#0D0D0D",
                        "accent": "#D94F2B",
                        "inactive": "#C8C2B4"
                    }
            else:
                # Fallback to current token values if not found (mainly for testing)
                theme_colors[t] = {
                    "bg": bg,
                    "bg2": bg2,
                    "fg": fg,
                    "accent": accent,
                    "inactive": inactive
                }

        # 3. Read active preview theme name
        preview_theme = theme_name
        preview_theme_path = Path("/tmp/dotfiles_preview_theme")
        if preview_theme_path.is_file():
            try:
                pt = preview_theme_path.read_text().strip()
                if pt in themes:
                    preview_theme = pt
            except Exception:
                pass

        # Dots indicator
        dots = []
        for t in themes:
            if t == preview_theme:
                dots.append("•")
            else:
                dots.append("◦")
        dots_str = " ".join(dots)

        # 4. Generate config.json (swaync-config)
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
                "label#theme-preview-title",
                "buttons-grid#theme-preview-image",
                "buttons-grid#theme-preview-palette",
                "buttons-grid#theme-preview-controls",
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
                    "image-radius": 4,
                    "blacklist": ["zen", "firefox", "chromium", "vesktop", "Vesktop", "discord", "Zen Browser", "zen-app"]
                },
                "volume": {
                    "label": "󰕾"
                },
                "buttons-grid#updates": {
                    "buttons-per-row": 1,
                    "actions": [
                        {
                            "label": "Check for Updates",
                            "command": f"hyprctl dispatch exec 'ghostty --class=com.system.update --title=\"System Update\" -e {Path.home()}/.config/waybar/scripts/system-update.sh'"
                        }
                    ]
                },
                "label#theme-preview-title": {
                    "text": f"Theme: {preview_theme}",
                    "clear-all-button": False
                },
                "buttons-grid#theme-preview-image": {
                    "buttons-per-row": 1,
                    "actions": [
                        {
                            "label": " ",
                            "command": "true"
                        }
                    ]
                },
                "buttons-grid#theme-preview-palette": {
                    "buttons-per-row": 1,
                    "actions": [
                        {
                            "label": " ",
                            "command": "true"
                        }
                    ]
                },
                "buttons-grid#theme-preview-controls": {
                    "buttons-per-row": 4,
                    "actions": [
                        {
                            "label": "◀",
                            "command": "/home/hugo2006alm/.local/bin/dotfiles action preview prev"
                        },
                        {
                            "label": dots_str,
                            "command": "true"
                        },
                        {
                            "label": "▶",
                            "command": "/home/hugo2006alm/.local/bin/dotfiles action preview next"
                        },
                        {
                            "label": "Selected" if preview_theme == theme_name else "Select",
                            "command": "true" if preview_theme == theme_name else f"/home/hugo2006alm/.local/bin/dotfiles configure --theme {preview_theme}"
                        }
                    ]
                }
            }
        }

        # 5. Generate style.css (swaync-style)
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

/* Hide scrollbar completamente */
.control-center scrollbar {{
  background: transparent;
  min-width: 0px;
  width: 0px;
}}
.control-center scrollbar slider {{
  background: transparent;
  min-width: 0px;
  width: 0px;
}}
.control-center viewport {{
  background: transparent;
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
  color: {fg};
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

/* ── Theme Preview Carousel ── */
#theme-preview-title {{
  font-size: 14px;
  font-weight: bold;
  color: {fg};
  margin: 12px 0 4px 0;
}}
"""

        # 6. Read active wallpaper for styling
        base_preview_theme = preview_theme.split("-")[0]
        preview_wp_dir = Path.home() / "wallpapers" / preview_theme
        if not preview_wp_dir.exists():
            preview_wp_dir = Path.home() / "wallpapers" / base_preview_theme

        preview_wallpapers = []
        if preview_wp_dir.is_dir():
            preview_wallpapers = sorted(
                list(preview_wp_dir.glob("*.jpg")) + list(preview_wp_dir.glob("*.png"))
            )

        preview_wallpaper_path = ""
        if preview_wallpapers:
            preview_wallpaper_path = str(preview_wallpapers[0].resolve())

        if preview_wallpaper_path:
            style_content += f"""
#theme-preview-image > flowbox > flowboxchild > button {{
  background-image: url("{preview_wallpaper_path}");
  background-size: cover;
  background-position: center;
  min-height: 220px;
  min-width: 220px;
  margin: 12px 64px;
  border: 8px solid {bg2};
  outline: 2px solid {border};
  border-radius: 0px;
}}
#theme-preview-image > flowbox > flowboxchild > button:hover,
#theme-preview-image > flowbox > flowboxchild > button:active,
#theme-preview-image > flowbox > flowboxchild > button:focus {{
  background-image: url("{preview_wallpaper_path}");
  background-size: cover;
  background-position: center;
  outline: 2px solid {border};
  border-color: {bg2};
  box-shadow: none;
}}
"""
        else:
            style_content += f"""
#theme-preview-image > flowbox > flowboxchild > button {{
  background-color: {bg2};
  min-height: 220px;
  min-width: 220px;
  margin: 12px 64px;
  border: 8px solid {bg2};
  outline: 2px solid {border};
  border-radius: 0px;
}}
#theme-preview-image > flowbox > flowboxchild > button:hover,
#theme-preview-image > flowbox > flowboxchild > button:active,
#theme-preview-image > flowbox > flowboxchild > button:focus {{
  background-color: {bg2};
  outline: 2px solid {border};
  border-color: {bg2};
  box-shadow: none;
}}
"""

        p_colors = theme_colors.get(preview_theme, {
            "bg": bg,
            "bg2": bg2,
            "fg": fg,
            "accent": accent,
            "inactive": inactive
        })
        p_bg = p_colors.get("bg", bg)
        p_bg2 = p_colors.get("bg2", bg2)
        p_fg = p_colors.get("fg", fg)
        p_accent = p_colors.get("accent", accent)
        p_inactive = p_colors.get("inactive", inactive)

        style_content += f"""
#theme-preview-palette > flowbox > flowboxchild > button {{
  background: linear-gradient(to right, {p_bg} 20%, {p_bg2} 20%, {p_bg2} 40%, {p_fg} 40%, {p_fg} 60%, {p_accent} 60%, {p_accent} 80%, {p_inactive} 80%);
  min-height: 48px;
  border: 2px solid {border};
  border-radius: 0px;
  margin: 8px 16px;
}}
#theme-preview-palette > flowbox > flowboxchild > button:hover,
#theme-preview-palette > flowbox > flowboxchild > button:active,
#theme-preview-palette > flowbox > flowboxchild > button:focus {{
  background: linear-gradient(to right, {p_bg} 20%, {p_bg2} 20%, {p_bg2} 40%, {p_fg} 40%, {p_fg} 60%, {p_accent} 60%, {p_accent} 80%, {p_inactive} 80%);
  border-color: {border};
  box-shadow: none;
}}

#theme-preview-controls {{
  margin: 8px 0;
}}
#theme-preview-controls > flowbox > flowboxchild > button {{
  background: {bg2};
  border: 2px solid {border};
  border-radius: 0px;
  color: {fg};
  padding: 6px 12px;
  font-weight: bold;
  font-size: 12px;
  margin: 4px;
}}
#theme-preview-controls > flowbox > flowboxchild > button:hover {{
  background: {accent};
  color: {bg};
  border-color: {accent};
}}
"""

        if preview_theme == theme_name:
            style_content += f"""
#theme-preview-controls > flowbox > flowboxchild:nth-child(4) > button {{
  background: {accent};
  color: {bg};
  border-color: {accent};
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

@keyframes fade-out {{
  from {{
    opacity: 1;
    margin-top: 8px;
    margin-bottom: 8px;
    padding: 12px;
  }}
  to {{
    opacity: 0;
    margin-top: 0px;
    margin-bottom: 0px;
    padding: 0px;
  }}
}}
.notification.removed {{
  animation: fade-out 200ms ease-in-out forwards;
}}
"""

        return [
            GeneratedArtifact(artifact_id="swaync-config", content=json.dumps(config_data, indent=2)),
            GeneratedArtifact(artifact_id="swaync-style", content=style_content)
        ]
