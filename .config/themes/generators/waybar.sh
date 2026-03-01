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
accent2=$(get accent2)
accent_fg=$(get accent_fg)
active=$(get active)
inactive=$(get inactive)
urgent=$(get urgent)
selection=$(get selection)
selection_fg=$(get selection_fg)
waybar_bg=$(get waybar_bg)
waybar_fg=$(get waybar_fg)
waybar_acc=$(get waybar_acc)

font_mono=$(gets font_mono)
font_size_sm=$(gets font_size_sm)
font_size_md=$(gets font_size_md)
font_size_lg=$(gets font_size_lg)

cat > ~/.config/waybar/_colors.scss << EOF
// Auto-generated from themes/$THEME/colors.toml — do not edit directly
\$background:   $background;
\$background2:  $background2;
\$foreground:   $foreground;
\$foreground2:  $foreground2;
\$border:       $border;
\$accent:       $accent;
\$accent2:      $accent2;
\$accent_fg:    $accent_fg;
\$active:       $active;
\$inactive:     $inactive;
\$urgent:       $urgent;
\$selection:    $selection;
\$selection_fg: $selection_fg;
\$waybar_bg:    $waybar_bg;
\$waybar_fg:    $waybar_fg;
\$waybar_acc:   $waybar_acc;
\$font_mono:    "$font_mono";
\$font_size_sm: ${font_size_sm}px;
\$font_size_md: ${font_size_md}px;
\$font_size_lg: ${font_size_lg}px;
EOF

echo "Generated ~/.config/waybar/_colors.scss"

sassc ~/.config/waybar/style.scss ~/.config/waybar/style.css
echo "Compiled style.scss → style.css"
