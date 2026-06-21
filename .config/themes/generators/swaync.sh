#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

# Load colors and styles in a single pass (0ms overhead)
declare -A colors
while IFS= read -r line; do
  if [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*\"([^\"]+)\" ]]; then
    colors["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  elif [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*([0-9.]+) ]]; then
    colors["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  fi
done < "$TOML"

declare -A style
while IFS= read -r line; do
  if [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*\"([^\"]+)\" ]]; then
    style["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  elif [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*([0-9.]+) ]]; then
    style["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  fi
done < "$STYLE"

background="${colors[background]}"
background2="${colors[background2]}"
foreground="${colors[foreground]}"
foreground2="${colors[foreground2]}"
border="${colors[border]}"
accent="${colors[accent]}"
inactive="${colors[inactive]}"
font_mono="${style[font_mono]}"

mkdir -p ~/.config/swaync

cat > ~/.config/swaync/style.css << EOF
/* Auto-generated from themes/$THEME/colors.toml — do not edit directly */

* {
  font-family: "$font_mono", monospace;
  box-shadow: none;
}

/* ── Control Center ── */
.control-center {
  background: $background;
  border: 3px solid $border;
  border-radius: 0px;
  color: $foreground;
  padding: 16px;
}

/* ── Title Widget ── */
.widget-title {
  margin: 8px 0;
}
.widget-title > label {
  font-size: 16px;
  font-weight: bold;
  color: $foreground;
}
.widget-title > button {
  background: $background2;
  border: 2px solid $border;
  border-radius: 0px;
  color: $foreground;
  padding: 6px 12px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
}
.widget-title > button:hover {
  background: $accent;
  color: $background;
  border-color: $accent;
}

/* ── DND Widget ── */
.widget-dnd {
  margin: 8px 0;
  font-size: 13px;
  color: $foreground;
}
.widget-dnd > switch {
  background: $background2;
  border: 2px solid $border;
  border-radius: 0px;
}
.widget-dnd > switch:checked {
  background: $accent;
  border-color: $accent;
}
.widget-dnd > switch slider {
  background: $foreground;
  border-radius: 0px;
}

/* ── MPRIS Widget ── */
.widget-mpris {
  background: $background2;
  border: 2px solid $border;
  border-radius: 0px;
  padding: 12px;
  margin: 8px 0;
}
.widget-mpris-player {
  padding: 4px;
}
.widget-mpris-title {
  font-weight: bold;
  font-size: 13px;
}
.widget-mpris-subtitle {
  font-size: 11px;
  color: $foreground2;
}

/* ── Sliders (Volume) ── */
.widget-volume {
  background: $background2;
  border: 2px solid $border;
  border-radius: 0px;
  padding: 8px 12px;
  margin: 6px 0;
}
.widget-volume scale trough {
  background: $inactive;
  border-radius: 0px;
  min-height: 8px;
}
.widget-volume scale highlight {
  background: $accent;
  border-radius: 0px;
}

/* ── Buttons Grid ── */
.widget-buttons-grid {
  margin: 8px 0;
}
.widget-buttons-grid > flowbox > flowboxchild > button {
  background: $background2;
  border: 2px solid $border;
  border-radius: 0px;
  color: $foreground;
  padding: 8px 12px;
  font-weight: bold;
  font-size: 11px;
  text-transform: uppercase;
  margin: 4px;
}
.widget-buttons-grid > flowbox > flowboxchild > button:hover {
  background: $accent;
  color: $background;
  border-color: $accent;
}
.widget-buttons-grid > flowbox > flowboxchild > button.active {
  background: $accent;
  color: $background;
  border-color: $accent;
}

/* ── Notifications ── */
.notification {
  background: $background2;
  border: 2px solid $border;
  border-radius: 0px;
  margin: 8px 0;
  padding: 12px;
}
.notification-row {
  outline: none;
}
.notification-row:hover {
  background: transparent;
}
.notification-content {
  padding: 4px;
}
.notification-title {
  font-weight: bold;
  font-size: 13px;
  color: $foreground;
}
.notification-body {
  font-size: 11px;
  color: $foreground2;
}
.notification-action {
  background: $background;
  border: 2px solid $border;
  border-radius: 0px;
  color: $foreground;
  font-size: 11px;
  font-weight: bold;
}
.notification-action:hover {
  background: $accent;
  color: $background;
}
EOF

echo "Generated ~/.config/swaync/style.css"
