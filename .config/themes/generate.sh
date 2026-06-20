#!/bin/bash

THEME="${1:-$(cat ~/.config/themes/current)}"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

if [[ ! -f "$TOML" ]]; then
  echo "Theme '$THEME' not found at $TOML"
  exit 1
fi

echo "$THEME" > ~/.config/themes/current

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

chmod +x "$DIR/generators/"*.sh
for generator in "$DIR/generators/"*.sh; do
  bash "$generator" "$THEME"
done



get() { grep "^$1 " "$TOML" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
hex() { echo "${1#\#}"; }

## Vesktop Generator Block
echo "Generating Vesktop Theme..."
mkdir -p ~/.config/vesktop/themes

cat << EOF > ~/.config/vesktop/themes/shade-raid.theme.css
/**
 * @name Shade Raid
 * @author Generator
 * @version 1.0.0
 * @description Ink on paper theme
 */

/* Block OS window transparency and make main containers opaque */
html, body, #app-mount, .app-mount, [class^="appMount_"], [class^="bg_"] {
    background-color: $(get background) !important;
    background-image: none !important;
}

/* Override all native Discord color variables */
:root, .theme-dark, .theme-light {
    --background-primary: $(get background) !important;
    --background-secondary: $(get background2) !important;
    --background-secondary-alt: $(get inactive) !important;
    --background-tertiary: $(get background2) !important;
    --background-floating: $(get background) !important;
    --background-nested-floating: $(get background2) !important;
    --bg-overlay-chat: $(get background) !important;
    --bg-overlay-app-frame: $(get background2) !important;
    --bg-base-primary: $(get background) !important;
    --bg-base-secondary: $(get background2) !important;
    --bg-base-tertiary: $(get background2) !important;
    --background-message-hover: rgba(127, 127, 127, 0.05) !important;
    --channeltextarea-background: $(get background2) !important;
    --info-positive-background: $(get background2) !important;
    --info-warning-background: $(get background2) !important;
    --info-danger-background: $(get background2) !important;
    --text-normal: $(get foreground) !important;
    --text-muted: $(get foreground2) !important;
    --text-link: $(get accent) !important;
    --header-primary: $(get foreground) !important;
    --header-secondary: $(get foreground2) !important;
    --interactive-normal: $(get foreground) !important;
    --interactive-hover: $(get accent) !important;
    --interactive-active: $(get accent_fg) !important;
    --interactive-muted: $(get inactive) !important;
    --brand-experiment: $(get accent) !important;
    --brand-experiment-500: $(get accent) !important;
    --brand-experiment-560: $(get accent) !important;
    --brand-experiment-600: $(get accent) !important;
    --button-danger-background: $(get urgent) !important;
    --background-modifier-selected: $(get selection) !important;
    --background-modifier-hover: rgba(127, 127, 127, 0.1) !important;
    --background-modifier-active: rgba(127, 127, 127, 0.2) !important;
    --background-modifier-accent: rgba(127, 127, 127, 0.1) !important;
    --scrollbar-auto-thumb: $(get foreground) !important;
    --scrollbar-auto-track: transparent !important;
    --scrollbar-thin-thumb: $(get foreground) !important;
    --scrollbar-thin-track: transparent !important;
    --border-radius: 0px !important;
}

/* Zero border radius */
* {
    border-radius: 0 !important;
    box-shadow: none !important;
}
::-webkit-scrollbar {
    width: 8px !important;
}
::-webkit-scrollbar-thumb {
    background: $(get foreground) !important;
    border-radius: 0 !important;
}
EOF

echo "Done — theme: $THEME"

# Trigger Plymouth sync asynchronously safely using a pending flag
touch /tmp/plymouth_sync_pending
sudo /home/hugo2006alm/dotfiles/.config/themes/sync-plymouth.sh > /dev/null 2>&1 &
