#!/bin/bash
# Reads the global colors.toml and updates /etc/greetd/regreet.toml.
# Copies the LAST used wallpaper (blurred) to /etc/greetd/regreet-background.jpg
# so the login screen always matches the desktop wallpaper.

THEME="$1"
if [ -z "$THEME" ]; then
  exit 1
fi

TOML="$HOME/.config/themes/$THEME/colors.toml"
if [ ! -f "$TOML" ]; then
  exit 1
fi

CONFIG_FILE="/etc/greetd/regreet.toml"
BG_FILE="/etc/greetd/regreet-background.jpg"

if [ ! -w "$CONFIG_FILE" ]; then
    echo "greetd.sh: no write access to $CONFIG_FILE — skipping" >&2
    exit 0
fi

# ── Determine background source ──────────────────────────────────────────────
# Prefer the last used wallpaper; fall back to a random one from the theme dir
LAST_WALL=$(cat "$HOME/.cache/shade-raid/last_wallpaper" 2>/dev/null)

if [ -n "$LAST_WALL" ] && [ -f "$LAST_WALL" ]; then
    SRC_WALL="$LAST_WALL"
else
    # Fallback: pick a random wallpaper from the theme directory
    BASE_THEME="${THEME%-*}"
    if [ -d "$HOME/wallpapers/$THEME" ]; then
        WALLPAPERS_DIR="$HOME/wallpapers/$THEME"
    elif [ -d "$HOME/wallpapers/$BASE_THEME" ]; then
        WALLPAPERS_DIR="$HOME/wallpapers/$BASE_THEME"
    fi

    if [ -n "$WALLPAPERS_DIR" ]; then
        SRC_WALL=$(find -L "$WALLPAPERS_DIR" -type f \( -iname "*.jpg" -o -iname "*.png" \) | shuf -n 1)
    fi
fi

# ── Apply gaussian blur with ImageMagick and copy to /etc/greetd/ ────────────
if [ -n "$SRC_WALL" ] && [ -f "$SRC_WALL" ]; then
    TMPFILE=$(mktemp /tmp/greetd-bg-XXXXXX.jpg)
    convert "$(readlink -f "$SRC_WALL")" \
        -filter Gaussian \
        -blur 0x20 \
        -modulate 70 \
        "$TMPFILE" 2>/dev/null

    if [ $? -eq 0 ]; then
        cp "$TMPFILE" "$BG_FILE"
        echo "greetd.sh: blurred background updated → $BG_FILE"
    else
        echo "greetd.sh: ImageMagick blur failed, using source as-is" >&2
        cp "$(readlink -f "$SRC_WALL")" "$BG_FILE"
    fi
    rm -f "$TMPFILE"
fi

# ── Write regreet.toml ───────────────────────────────────────────────────────
IS_DARK=false
[[ "$THEME" == *"-dark"* ]] && IS_DARK=true

cat > "$CONFIG_FILE" <<EOF
[background]
path = "$BG_FILE"
fit = "Cover"

[GTK]
application_prefer_dark_theme = $IS_DARK
EOF

echo "greetd.sh: regreet.toml written — theme=$THEME dark=$IS_DARK"
