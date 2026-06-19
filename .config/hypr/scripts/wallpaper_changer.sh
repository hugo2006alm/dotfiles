#!/bin/bash
THEME=$(cat ~/.config/themes/current 2>/dev/null || echo "shade-raid")
WALLPAPERS_DIR="$HOME/wallpapers/$THEME"

if [ ! -d "$WALLPAPERS_DIR" ]; then
    notify-send "Wallpaper Error" "Directory $WALLPAPERS_DIR not found"
    exit 1
fi

RANDOM_WALL=$(find -L "$WALLPAPERS_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" \) | shuf -n 1)

if [ -n "$RANDOM_WALL" ]; then
    # We follow the symlink or use the target file
    swww img "$(readlink -f "$RANDOM_WALL")" --transition-type wipe --transition-angle 30
    notify-send "Wallpaper Changed" "$(basename "$RANDOM_WALL")"
else
    notify-send "Wallpaper Error" "No wallpapers found"
fi
