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

# Vesktop Generator Block
echo "Generating Vesktop Theme..."
mkdir -p ~/.config/vesktop/themes

cat << 'EOF' > ~/.config/vesktop/themes/shade-raid.theme.css
/**
 * @name Shade Raid
 * @author Generator
 * @version 1.0.0
 * @description Ink on paper theme
 */
#app-mount .theme-light, #app-mount .theme-dark, .theme-dark, .theme-light, :root {
EOF
echo "  --background-primary: $(get background) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-secondary: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-secondary-alt: $(get inactive) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-tertiary: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-floating: $(get background) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-nested-floating: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --bg-overlay-chat: $(get background) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --bg-overlay-app-frame: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --bg-base-primary: $(get background) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --bg-base-secondary: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --bg-base-tertiary: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-message-hover: rgba(127, 127, 127, 0.05) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --channeltextarea-background: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --info-positive-background: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --info-warning-background: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --info-danger-background: $(get background2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --text-normal: $(get foreground) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --text-muted: $(get foreground2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --text-link: $(get accent) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --header-primary: $(get foreground) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --header-secondary: $(get foreground2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --interactive-normal: $(get foreground) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --interactive-hover: $(get accent) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --interactive-active: $(get accent_fg) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --interactive-muted: $(get inactive) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --brand-experiment: $(get accent) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --brand-experiment-500: $(get accent) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --brand-experiment-560: $(get accent) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --brand-experiment-600: $(get accent) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --button-danger-background: $(get urgent) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --background-modifier-selected: $(get selection) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-modifier-hover: rgba(127, 127, 127, 0.1) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-modifier-active: rgba(127, 127, 127, 0.2) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-modifier-accent: rgba(127, 127, 127, 0.1) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --scrollbar-auto-thumb: $(get foreground) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --scrollbar-auto-track: transparent !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --scrollbar-thin-thumb: $(get foreground) !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --scrollbar-thin-track: transparent !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --border-radius: 0px !important;" >> ~/.config/vesktop/themes/shade-raid.theme.css
cat << 'EOF' >> ~/.config/vesktop/themes/shade-raid.theme.css
}
body, #app-mount, .appMount_ea7e65 {
    background-color: var(--background-primary) !important;
}
.app_a3002d, .bg_d4b6c5, .chat_f75fb0, .wrapper_fc8177, .users__260e1, .sidebar__5e434, .panels_a4d4d9, .container__2637a, .wrapper_bd2abe {
    background: transparent !important;
    background-color: transparent !important;
}
* {
    border-radius: 0 !important;
    box-shadow: none !important;
}
::-webkit-scrollbar {
    width: 8px !important;
}
::-webkit-scrollbar-thumb {
    background: var(--scrollbar-auto-thumb) !important;
    border-radius: 0 !important;
}
EOF

echo "Done — theme: $THEME"

# Trigger Plymouth sync asynchronously safely using a pending flag
touch /tmp/plymouth_sync_pending
sudo /home/hugo2006alm/dotfiles/.config/themes/sync-plymouth.sh > /dev/null 2>&1 &
