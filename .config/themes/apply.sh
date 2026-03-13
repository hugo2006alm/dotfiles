#!/bin/bash

THEME="${1:-$(cat ~/.config/themes/current)}"

~/.config/themes/generate.sh "$THEME"
~/.config/hypr/scripts/gen-drawers.sh

hyprctl reload >>/dev/null 2>&1
pkill waybar; waybar >> /dev/null 2>&1 &
pkill mako; mako >> /dev/null 2>&1 &
pkill -USR2 ghostty 2>/dev/null || true
pkill walker 2>/dev/null; sleep 0.2; walker --gapplication-service >> /dev/null 2>&1 &

echo "Applied theme: $THEME"
