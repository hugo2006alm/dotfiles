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

  # Generate regreet CSS
  CSS_FILE="/etc/greetd/regreet.css"
  
  # Fetch theme colors
  get() { grep "^\$1 " "$TOML" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
  bg="\$(get background)"
  fg="\$(get foreground)"
  accent="\$(get accent)"

  cat > "\$CSS_FILE" << EOF
* {
    font-family: "JetBrains Mono Nerd Font", "Inter", sans-serif;
}

window {
    background-color: transparent;
}

box.login-box {
    background-color: rgba(0, 0, 0, 0.4);
    border-radius: 12px;
    padding: 24px;
}

entry {
    background-color: $bg;
    color: $fg;
    border: 2px solid $accent;
    border-radius: 6px;
}

button {
    background-color: $accent;
    color: $bg;
    border-radius: 6px;
    font-weight: bold;
}

button:hover {
    background-color: shade($accent, 1.2);
}
EOF

fi
