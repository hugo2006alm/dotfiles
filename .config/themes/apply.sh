#!/bin/bash

THEME="${1:-$(cat ~/.config/themes/current)}"

~/.config/themes/generate.sh "$THEME"

# Reload Hyprland
hyprctl reload

# Reload Waybar
pkill waybar && waybar &

# Reload Mako
pkill mako && mako &

echo "Applied theme: $THEME"
