#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

get()  { grep "^$1 " "$TOML"  | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
gets() { grep "^$1 " "$STYLE" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }

background=$(get background)
background2=$(get background2)
foreground=$(get foreground)
foreground2=$(get foreground2)
border=$(get border)
accent=$(get accent)
inactive=$(get inactive)
font_mono=$(gets font_mono)
font_size_sm=$(gets font_size_sm)
font_size_md=$(gets font_size_md)

mkdir -p ~/.config/walker/themes/$THEME

cat > ~/.config/walker/themes/$THEME/_colors.scss << EOF
// Auto-generated from themes/$THEME/colors.toml — do not edit directly
\$background:   $background;
\$background2:  $background2;
\$foreground:   $foreground;
\$foreground2:  $foreground2;
\$border:       $border;
\$accent:       $accent;
\$inactive:     $inactive;
\$font_mono:    "$font_mono";
\$font_size_sm: ${font_size_sm}px;
\$font_size_md: ${font_size_md}px;
EOF

echo "Generated ~/.config/walker/themes/$THEME/_colors.scss"

cp ~/.config/walker/themes/$THEME/_colors.scss ~/.config/walker/themes/_colors.scss

cd ~/.config/walker/themes
sassc -I $THEME \
  style.scss \
  $THEME/style.css
echo "Compiled walker style.scss → style.css"

cat > ~/.config/walker/config.toml << EOF
theme = "$THEME"

[search]
placeholder = "Search..."

[[modules]]
name = "applications"
placeholder = "Applications"

[[modules]]
name = "runner"
placeholder = "Run"

[[modules]]
name = "clipboard"
placeholder = "Clipboard"
EOF

echo "Generated ~/.config/walker/config.toml"
echo "Added correct theme to config.toml"
