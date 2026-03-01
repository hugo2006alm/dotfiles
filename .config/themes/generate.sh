#!/bin/bash

THEME="${1:-$(cat ~/.config/themes/current)}"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

if [[ ! -f "$TOML" ]]; then
  echo "Theme '$THEME' not found at $TOML"
  exit 1
fi

echo "$THEME" > ~/.config/themes/current

# ── Parse helpers ─────────────────────────
get() {
  grep "^$1 " "$TOML" | head -1 | sed 's/.*= *"\(.*\)"/\1/'
}

gets() {
  grep "^$1 " "$STYLE" | head -1 | sed 's/.*= *"\(.*\)"/\1/'
}

hex() { echo "${1#\#}"; }

# ── Read colors ───────────────────────────
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
shadow=$(get shadow)
shadow_alpha=$(get shadow_alpha)
notify_bg=$(get notify_bg)
notify_fg=$(get notify_fg)
notify_border=$(get notify_border)
lock_bg=$(get lock_bg)
lock_fg=$(get lock_fg)
lock_input=$(get lock_input)

# ── Read style ────────────────────────────
font_mono=$(gets font_mono)
font_display=$(gets font_display)
font_size_sm=$(gets font_size_sm)
font_size_md=$(gets font_size_md)
font_size_lg=$(gets font_size_lg)
cursor_theme=$(gets cursor_theme)
cursor_size=$(gets cursor_size)
border_size=$(gets border_size)
gaps_inner=$(gets gaps_inner)
gaps_outer=$(gets gaps_outer)
corner_radius=$(gets corner_radius)
shadow_offset_x=$(gets shadow_offset_x)
shadow_offset_y=$(gets shadow_offset_y)
shadow_range=$(gets shadow_range)
shadow_render_power=$(gets shadow_render_power)

# Convert shadow alpha to hex
shadow_alpha_hex=$(printf '%02X' $(awk "BEGIN {printf \"%d\", $shadow_alpha * 255}"))
shadow_rgba="$(hex $shadow)${shadow_alpha_hex}"

# ── Hyprland colors.conf ──────────────────
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

# ── Hyprland style.conf ───────────────────
cat > ~/.config/hypr/style.conf << EOF
# Auto-generated from themes/style.toml — do not edit directly
\$border_size    = $border_size
\$gaps_inner     = $gaps_inner
\$gaps_outer     = $gaps_outer
\$corner_radius  = $corner_radius
\$cursor_theme   = $cursor_theme
\$cursor_size    = $cursor_size
\$font_mono      = $font_mono
\$font_display   = $font_display
\$font_size_sm   = $font_size_sm
\$font_size_md   = $font_size_md
\$font_size_lg   = $font_size_lg
\$shadow_offset_x     = $shadow_offset_x
\$shadow_offset_y     = $shadow_offset_y
\$shadow_range        = $shadow_range
\$shadow_render_power = $shadow_render_power
EOF

echo "Generated ~/.config/hypr/style.conf"

# ── Waybar _colors.scss ───────────────────
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

# ── Compile SCSS → CSS ────────────────────
sassc ~/.config/waybar/style.scss ~/.config/waybar/style.css
echo "Compiled style.scss → style.css"

# ── Mako full config ──────────────────────
cat > ~/.config/mako/config << EOF
# Auto-generated — do not edit directly

# Position
anchor=top-right
margin=12
offset=0,8

# Size
width=360
height=120
padding=12

# Style
border-size=3
border-radius=0
font=Monaspace Radon 11

# Colors
background-color=$notify_bg
text-color=$notify_fg
border-color=$notify_border

# Timing
default-timeout=5000
ignore-timeout=0
max-visible=5

# Urgency — low
[urgency=low]
opacity=0.7

# Urgency — critical
[urgency=critical]
border-color=$urgent
text-color=$urgent
default-timeout=0
EOF

echo "Generated ~/.config/mako/config"

# ── Ghostty colors ────────────────────────
cat > ~/.config/ghostty/colors.conf << EOF
# Auto-generated — do not edit directly
background = $(hex $background)
foreground = $(hex $foreground)
font-family = $font_mono
font-size = $font_size_md
EOF

echo "Generated ~/.config/ghostty/colors.conf"

echo "Done — theme: $THEME"
