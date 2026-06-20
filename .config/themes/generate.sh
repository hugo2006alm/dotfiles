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
echo "/**
 * @name Shade Raid
 * @author Generator
 * @version 1.0.0
 * @description Ink on paper theme
 */
:root {
  --background-primary: $(get background);
  --background-secondary: $(get background2);
  --background-secondary-alt: $(get inactive);
  --background-tertiary: $(get background2);
  --text-normal: $(get foreground);
  --text-muted: $(get foreground2);
  --brand-experiment: $(get accent);
  --interactive-normal: $(get foreground);
  --interactive-hover: $(get accent);
  --interactive-active: $(get accent_fg);
  --background-modifier-selected: $(get foreground);
  --background-modifier-hover: rgba(13, 13, 13, 0.1);
  --border-radius: 0px;
}
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
" > ~/.config/vesktop/themes/shade-raid.theme.css

echo "Done — theme: $THEME"

# Trigger Plymouth sync asynchronously
sudo /home/hugo2006alm/dotfiles/.config/themes/sync-plymouth.sh > /dev/null 2>&1 &
