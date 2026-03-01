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

bash "$DIR/generators/hypr.sh"    "$THEME"
bash "$DIR/generators/waybar.sh"  "$THEME"
bash "$DIR/generators/mako.sh"    "$THEME"
bash "$DIR/generators/ghostty.sh" "$THEME"

echo "Done — theme: $THEME"
