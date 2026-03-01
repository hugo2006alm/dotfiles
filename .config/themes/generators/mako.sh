#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

get()  { grep "^$1 " "$TOML"  | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
gets() { grep "^$1 " "$STYLE" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }

notify_bg=$(get notify_bg)
notify_fg=$(get notify_fg)
notify_border=$(get notify_border)
urgent=$(get urgent)
font_mono=$(gets font_mono)
font_size_sm=$(gets font_size_sm)

mkdir -p ~/.config/mako

cat > ~/.config/mako/config << EOF
# Auto-generated — do not edit directly

# Position
anchor=top-right
margin=12

# Size
width=360
height=120
padding=12

# Style
border-size=3
border-radius=0
font=$font_mono $font_size_sm

# Colors
background-color=${notify_bg}FF
text-color=${notify_fg}FF
border-color=${notify_border}FF

# Timing
default-timeout=5000
ignore-timeout=1
max-visible=5

[urgency=low]
background-color=${notify_bg}AA
border-color=${notify_border}AA

[urgency=critical]
background-color=${notify_bg}FF
border-color=${urgent}FF
text-color=${urgent}FF
default-timeout=0
EOF

echo "Generated ~/.config/mako/config"
