#!/bin/bash

THEME="${1:-$(cat ~/.config/themes/current)}"

~/.config/themes/generate.sh "$THEME"
~/.config/hypr/scripts/gen-drawers.sh

hyprctl reload >>/dev/null 2>&1
pkill waybar; waybar >> /dev/null 2>&1 &
pkill mako; mako >> /dev/null 2>&1 &
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
    hyprctl dispatch togglespecialworkspace btop >/dev/null 2>&1 &
fi

echo "Applied theme: $THEME"
