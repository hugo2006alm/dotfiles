#!/bin/bash

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
THEME="${1:-$(cat ~/.config/themes/current)}"

# Update gsettings to match theme dark/light variant
if [[ "$THEME" == *-dark ]]; then
    gsettings set org.gnome.desktop.interface color-scheme "prefer-dark" 2>/dev/null || true
    gsettings set org.gnome.desktop.interface gtk-theme "Adwaita-dark" 2>/dev/null || true
    gsettings set org.gnome.desktop.interface icon-theme "Papirus-Dark" 2>/dev/null || true
else
    gsettings set org.gnome.desktop.interface color-scheme "prefer-light" 2>/dev/null || true
    gsettings set org.gnome.desktop.interface gtk-theme "Adwaita" 2>/dev/null || true
    gsettings set org.gnome.desktop.interface icon-theme "Papirus-Light" 2>/dev/null || true
fi

"$DIR/generate.sh" "$THEME"
"$DIR/../hypr/scripts/gen-drawers.sh"

hyprctl reload >>/dev/null 2>&1
pkill waybar; waybar >> /dev/null 2>&1 &
pkill swaync; swaync >> /dev/null 2>&1 &
pkill -USR2 ghostty 2>/dev/null || true

BTOP_WAS_RUNNING=false
if pgrep -x btop >/dev/null; then
    BTOP_WAS_RUNNING=true
    pkill -x btop 2>/dev/null || true
fi

pkill walker 2>/dev/null; sleep 0.2; walker --gapplication-service >> /dev/null 2>&1 &

if pgrep -x wlogout > /dev/null; then
    pkill -x wlogout
    wlogout >> /dev/null 2>&1 &
fi

if [ "$BTOP_WAS_RUNNING" = true ]; then
    sleep 0.3
    hyprctl dispatch 'hl.dsp.workspace.toggle_special("btop")' >/dev/null 2>&1 &
fi

echo "Applied theme: $THEME"
