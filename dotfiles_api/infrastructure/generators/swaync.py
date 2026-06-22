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

        content = f"""/* Auto-generated from themes/{theme_name}/colors.toml — do not edit directly */

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

/* ── Buttons Grid ── */
.widget-buttons-grid {{
  margin: 8px 0;
}}
.widget-buttons-grid > flowbox > flowboxchild > button {{
  background: {bg2};
  border: 2px solid {border};
  border-radius: 0px;
  color: {fg};
  padding: 8px 12px;
  font-weight: bold;
  font-size: 11px;
  text-transform: uppercase;
  margin: 4px;
}}
.widget-buttons-grid > flowbox > flowboxchild > button:hover {{
  background: {accent};
  color: {bg};
  border-color: {accent};
}}
.widget-buttons-grid > flowbox > flowboxchild > button.active {{
  background: {accent};
  color: {bg};
  border-color: {accent};
}}

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
            GeneratedArtifact(artifact_id="swaync-style", content=content)
        ]
