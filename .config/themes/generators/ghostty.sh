#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

get()  { grep "^$1 " "$TOML"  | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
gets() { grep "^$1 " "$STYLE" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
hex()  { echo "${1#\#}"; }

background=$(get background)
foreground=$(get foreground)
font_mono=$(gets font_mono)
font_size_md=$(gets font_size_md)

cat > ~/.config/ghostty/colors.conf << EOF
# Auto-generated — do not edit directly
background = $(hex $background)
foreground = $(hex $foreground)
font-family = $font_mono
font-size = $font_size_md
EOF

echo "Generated ~/.config/ghostty/colors.conf"
