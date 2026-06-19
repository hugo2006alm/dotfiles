#!/bin/bash
THEME=$(cat ~/.config/themes/current 2>/dev/null || echo "shade-raid")
BASE_THEME="${THEME%-*}" # Strips -dark or -light

# Try specific theme first, then fallback to base theme
if [ -d "$HOME/wallpapers/$THEME" ]; then
    WALLPAPERS_DIR="$HOME/wallpapers/$THEME"
elif [ -d "$HOME/wallpapers/$BASE_THEME" ]; then
    WALLPAPERS_DIR="$HOME/wallpapers/$BASE_THEME"
else
    notify-send "Wallpaper Error" "Directory $HOME/wallpapers/$THEME not found"
    exit 1
fi

RANDOM_WALL=$(find -L "$WALLPAPERS_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" \) | shuf -n 1)

if [ -n "$RANDOM_WALL" ]; then
    # We follow the symlink or use the target file
    awww img "$(readlink -f "$RANDOM_WALL")" --transition-type wipe --transition-angle 30
    notify-send "Wallpaper Changed" "$(basename "$RANDOM_WALL")"
else
    notify-send "Wallpaper Error" "No wallpapers found"
fi
