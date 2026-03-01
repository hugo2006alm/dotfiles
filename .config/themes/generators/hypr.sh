#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

get()  { grep "^$1 " "$TOML"  | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
gets() { grep "^$1 " "$STYLE" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
hex()  { echo "${1#\#}"; }

# Colors
background=$(get background)
background2=$(get background2)
foreground=$(get foreground)
foreground2=$(get foreground2)
border=$(get border)
accent=$(get accent)
accent2=$(get accent2)
active=$(get active)
inactive=$(get inactive)
urgent=$(get urgent)
shadow=$(get shadow)
shadow_alpha=$(get shadow_alpha)

# Style
border_size=$(gets border_size)
gaps_inner=$(gets gaps_inner)
gaps_outer=$(gets gaps_outer)
corner_radius=$(gets corner_radius)
cursor_theme=$(gets cursor_theme)
cursor_size=$(gets cursor_size)
font_mono=$(gets font_mono)
font_display=$(gets font_display)
font_size_sm=$(gets font_size_sm)
font_size_md=$(gets font_size_md)
font_size_lg=$(gets font_size_lg)
shadow_offset_x=$(gets shadow_offset_x)
shadow_offset_y=$(gets shadow_offset_y)
shadow_range=$(gets shadow_range)
shadow_render_power=$(gets shadow_render_power)

# Convert shadow alpha to hex
shadow_alpha_hex=$(printf '%02X' $(awk "BEGIN {printf \"%d\", $shadow_alpha * 255}"))
shadow_rgba="$(hex $shadow)${shadow_alpha_hex}"

cat > ~/.config/hypr/colors.conf << EOF
# Auto-generated from themes/$THEME/colors.toml — do not edit directly
\$background  = rgb($(hex $background))
\$background2 = rgb($(hex $background2))
\$foreground  = rgb($(hex $foreground))
\$foreground2 = rgb($(hex $foreground2))
\$border      = rgb($(hex $border))
\$accent      = rgb($(hex $accent))
\$accent2     = rgb($(hex $accent2))
\$active      = rgb($(hex $active))
\$inactive    = rgb($(hex $inactive))
\$urgent      = rgb($(hex $urgent))
\$shadow      = rgba($shadow_rgba)
EOF

echo "Generated ~/.config/hypr/colors.conf"

cat > ~/.config/hypr/style.conf << EOF
# Auto-generated from themes/style.toml — do not edit directly
\$border_size         = $border_size
\$gaps_inner          = $gaps_inner
\$gaps_outer          = $gaps_outer
\$corner_radius       = $corner_radius
\$cursor_theme        = $cursor_theme
\$cursor_size         = $cursor_size
\$font_mono           = $font_mono
\$font_display        = $font_display
\$font_size_sm        = $font_size_sm
\$font_size_md        = $font_size_md
\$font_size_lg        = $font_size_lg
\$shadow_offset_x     = $shadow_offset_x
\$shadow_offset_y     = $shadow_offset_y
\$shadow_range        = $shadow_range
\$shadow_render_power = $shadow_render_power
EOF

echo "Generated ~/.config/hypr/style.conf"
