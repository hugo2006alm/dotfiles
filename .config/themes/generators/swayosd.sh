#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"

get() { grep "^$1 " "$TOML" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }

background=$(get background)
foreground=$(get foreground)
accent=$(get accent)
inactive=$(get inactive)
shadow=$(get shadow)

# Fallbacks
[ -z "$background" ] && background="#F4EFE4"
[ -z "$foreground" ] && foreground="#0D0D0D"
[ -z "$accent"     ] && accent="#D94F2B"
[ -z "$inactive"   ] && inactive="#C8C2B4"
[ -z "$shadow"     ] && shadow="#0D0D0D"

mkdir -p ~/.config/swayosd

# Write _colors.scss for @import
cat > ~/.config/swayosd/_colors.scss << SCSS
// Auto-generated from themes/$THEME/colors.toml — do not edit directly
\$background: $background;
\$foreground: $foreground;
\$accent:     $accent;
\$inactive:   $inactive;
\$shadow:     $shadow;
SCSS

# Compile SCSS → CSS
sassc ~/.config/swayosd/style.scss ~/.config/swayosd/style.css
echo "Generated ~/.config/swayosd/style.css"

# Reload swayosd-server if running (picks up new stylesheet)
if pgrep -x swayosd-server > /dev/null; then
    pkill -x swayosd-server
    # Wait a tiny bit for it to shutdown
    sleep 0.2
    hyprctl dispatch "hl.dsp.exec_cmd('swayosd-server --style $HOME/.config/swayosd/style.css')" > /dev/null
    echo "Reloaded swayosd-server"
fi

