#!/bin/bash
# update-greetd-wallpaper.sh
# Blurs a wallpaper and copies it to /etc/greetd/ for the regreet login screen.
# Usage: update-greetd-wallpaper.sh [/path/to/wallpaper.jpg]
# Falls back to ~/.cache/shade-raid/last_wallpaper if no argument given.

SRC="${1:-$(cat "$HOME/.cache/shade-raid/last_wallpaper" 2>/dev/null)}"
DEST="/etc/greetd/regreet-background.jpg"

if [ -z "$SRC" ] || [ ! -f "$SRC" ]; then
    echo "update-greetd-wallpaper: no source wallpaper found" >&2
    exit 1
fi

# Blur with ImageMagick: gaussian blur radius 0x20, also slightly darken
TMPFILE=$(mktemp /tmp/greetd-bg-XXXXXX.jpg)
convert "$SRC" \
    -filter Gaussian \
    -blur 0x20 \
    -modulate 70 \
    "$TMPFILE"

if [ $? -eq 0 ]; then
    # Copy to /etc/greetd — this requires write permission.
    # Run this script via sudoers or chown /etc/greetd/regreet-background.jpg to the user.
    cp "$TMPFILE" "$DEST" 2>/dev/null || {
        # Try sudo cp as a fallback (non-interactive, only works if NOPASSWD sudoers rule exists)
        sudo cp "$TMPFILE" "$DEST" 2>/dev/null
    }
    rm -f "$TMPFILE"
    echo "update-greetd-wallpaper: updated $DEST"
else
    rm -f "$TMPFILE"
    echo "update-greetd-wallpaper: ImageMagick failed" >&2
    exit 1
fi
