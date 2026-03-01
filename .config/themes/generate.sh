#!/bin/bash

THEME="${1:-$(cat ~/.config/themes/current)}"
TOML="$HOME/.config/themes/$THEME/colors.toml"

if [[ ! -f "$TOML" ]]; then
  echo "Theme '$THEME' not found at $TOML"
  exit 1
fi

echo "$THEME" > ~/.config/themes/current

# ── Parse helper ──────────────────────────
get() {
  grep "^$1 " "$TOML" | head -1 | sed 's/.*= *"\(.*\)"/\1/'
}

# strip # from hex
hex() { echo "${1#\#}"; }

# ── Read all colors ───────────────────────
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

# Convert shadow alpha (0.0-1.0) to hex
shadow_alpha_hex=$(printf '%02X' $(echo "$shadow_alpha * 255 / 1" | bc))
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
EOF

echo "Generated ~/.config/waybar/_colors.scss"

# ── Compile SCSS → CSS ────────────────────
sassc ~/.config/waybar/style.scss ~/.config/waybar/style.css
echo "Compiled style.scss → style.css"

# ── Mako colors.conf ──────────────────────
cat > ~/.config/mako/colors.conf << EOF
# Auto-generated from themes/$THEME/colors.toml — do not edit directly
background-color=$notify_bg
text-color=$notify_fg
border-color=$notify_border
EOF

echo "Generated ~/.config/mako/colors.conf"

# ── Ghostty colors ────────────────────────
cat > ~/.config/ghostty/colors.conf << EOF
# Auto-generated from themes/$THEME/colors.toml — do not edit directly
background = $(hex $background)
foreground = $(hex $foreground)
EOF

echo "Generated ~/.config/ghostty/colors.conf"

echo "Done — theme: $THEME"
