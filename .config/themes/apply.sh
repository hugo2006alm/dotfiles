#!/bin/bash

THEME="${1:-$(cat ~/.config/themes/current)}"

~/.config/themes/generate.sh "$THEME"

hyprctl reload >>/dev/null 2>&1
pkill waybar; waybar >> /dev/null 2>&1 &
pkill mako; mako >> /dev/null 2>&1 &

echo "Applied theme: $THEME"
