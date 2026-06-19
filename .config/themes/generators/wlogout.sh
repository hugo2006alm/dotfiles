#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"

get()  { grep "^$1 " "$TOML"  | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }

background=$(get background)
background2=$(get background2)
foreground=$(get foreground)
accent=$(get accent)
accent_fg=$(get accent_fg)
shadow=$(get shadow)

# Fallbacks
[ -z "$background" ] && background="#16130F"
[ -z "$background2" ] && background2="#201C17"
[ -z "$foreground" ] && foreground="#F4EFE4"
[ -z "$accent" ] && accent="#E8623E"
[ -z "$accent_fg" ] && accent_fg="#16130F"
[ -z "$shadow" ] && shadow="#000000"

cat > ~/.config/wlogout/_colors.scss << SCSS
// Auto-generated from themes/$THEME/colors.toml — do not edit directly
\$background: $background;
\$background2: $background2;
\$foreground: $foreground;
\$accent: $accent;
\$accent_fg: $accent_fg;
\$shadow: $shadow;
SCSS

echo "Generated ~/.config/wlogout/_colors.scss"

sassc ~/.config/wlogout/style.scss ~/.config/wlogout/style.css
echo "Compiled style.scss → style.css for wlogout"
