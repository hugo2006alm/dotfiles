#!/bin/bash

# Reads the global colors.toml and generates regreet configuration
# Writes to /etc/greetd/regreet.toml and copies wallpaper to /etc/greetd/regreet-background.jpg

THEME="$1"
if [ -z "$THEME" ]; then
  exit 1
fi

TOML="$HOME/.config/themes/$THEME/colors.toml"

if [ ! -f "$TOML" ]; then
  exit 1
fi

# Pick a random wallpaper
BASE_THEME="${THEME%-*}"
if [ -d "$HOME/wallpapers/$THEME" ]; then
    WALLPAPERS_DIR="$HOME/wallpapers/$THEME"
elif [ -d "$HOME/wallpapers/$BASE_THEME" ]; then
    WALLPAPERS_DIR="$HOME/wallpapers/$BASE_THEME"
fi

CONFIG_FILE="/etc/greetd/regreet.toml"
BG_FILE="/etc/greetd/regreet-background.jpg"

if [ -w "$CONFIG_FILE" ]; then
  
  if [ -n "$WALLPAPERS_DIR" ]; then
    RANDOM_WALL=$(find -L "$WALLPAPERS_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" \) | shuf -n 1)
    if [ -n "$RANDOM_WALL" ]; then
      cp "$(readlink -f "$RANDOM_WALL")" "$BG_FILE"
      chmod 666 "$BG_FILE"
    fi
  fi

  IS_DARK=true
  if [[ "$THEME" == *"-light"* ]]; then
      IS_DARK=false
  fi

  cat > "$CONFIG_FILE" << EOF
[background]
path = "$BG_FILE"
fit = "Cover"

[GTK]
application_prefer_dark_theme = $IS_DARK
EOF

fi
