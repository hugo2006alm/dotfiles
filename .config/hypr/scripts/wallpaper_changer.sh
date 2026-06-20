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
    REAL_WALL=$(readlink -f "$RANDOM_WALL")
    awww img "$REAL_WALL" --transition-type wipe --transition-angle 30
    notify-send "Wallpaper Changed" "$(basename "$REAL_WALL")"

    # Persist last wallpaper path (used by awww restore on next login)
    mkdir -p "$HOME/.cache/shade-raid"
    echo "$REAL_WALL" > "$HOME/.cache/shade-raid/last_wallpaper"

    # Update greetd blurred background in the background
    if [ -x "$HOME/.config/themes/scripts/update-greetd-wallpaper.sh" ]; then
        "$HOME/.config/themes/scripts/update-greetd-wallpaper.sh" "$REAL_WALL" &
    fi
else
    notify-send "Wallpaper Error" "No wallpapers found"
fi
