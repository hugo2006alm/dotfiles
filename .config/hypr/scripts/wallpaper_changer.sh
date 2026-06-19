#!/bin/bash
WALLPAPERS_DIR="$HOME/wallpapers/shade-raid"

if [ ! -d "$WALLPAPERS_DIR" ]; then
    notify-send "Wallpaper Error" "Directory $WALLPAPERS_DIR not found"
    exit 1
fi

RANDOM_WALL=$(find "$WALLPAPERS_DIR" -type f -name "*.jpg" -o -name "*.png" | shuf -n 1)

if [ -n "$RANDOM_WALL" ]; then
    # We follow the symlink or use the target file
    swww img "$(readlink -f "$RANDOM_WALL")" --transition-type wipe --transition-angle 30
    notify-send "Wallpaper Changed" "$(basename "$RANDOM_WALL")"
else
    notify-send "Wallpaper Error" "No wallpapers found"
fi
