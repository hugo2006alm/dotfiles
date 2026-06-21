#!/bin/bash
# shellcheck disable=SC2129

THEME="${1:-$(cat ~/.config/themes/current)}"
TOML="$HOME/.config/themes/$THEME/colors.toml"

if [[ ! -f "$TOML" ]]; then
  echo "Theme '$THEME' not found at $TOML"
  exit 1
fi

echo "$THEME" > ~/.config/themes/current

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

chmod +x "$DIR/generators/"*.sh
for generator in "$DIR/generators/"*.sh; do
  bash "$generator" "$THEME" &
done
wait

# Load colors from TOML in a single pass into a bash associative array (0ms, 0 processes)
declare -A colors
while IFS= read -r line; do
  if [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*\"([^\"]+)\" ]]; then
    colors["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  elif [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*([0-9.]+) ]]; then
    colors["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  fi
done < "$TOML"

get() { echo "${colors[$1]}"; }
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
.theme-dark, .theme-light, :root {
EOF
echo "  --background-primary: $(get background);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-secondary: $(get background2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-secondary-alt: $(get inactive);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-tertiary: $(get background2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-floating: $(get background);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-nested-floating: $(get background2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-message-hover: rgba(0, 0, 0, 0.05);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --channeltextarea-background: $(get background2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --info-positive-background: $(get background2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --info-warning-background: $(get background2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --info-danger-background: $(get background2);" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --text-normal: $(get foreground);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --text-muted: $(get foreground2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --text-link: $(get accent);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --header-primary: $(get foreground);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --header-secondary: $(get foreground2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --interactive-normal: $(get foreground);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --interactive-hover: $(get accent);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --interactive-active: $(get accent_fg);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --interactive-muted: $(get inactive);" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --brand-experiment: $(get accent);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --brand-experiment-500: $(get accent);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --brand-experiment-560: $(get accent);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --brand-experiment-600: $(get accent);" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --button-danger-background: $(get urgent);" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --background-modifier-selected: $(get selection);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-modifier-hover: rgba(127, 127, 127, 0.1);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-modifier-active: rgba(127, 127, 127, 0.2);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --background-modifier-accent: rgba(127, 127, 127, 0.1);" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --scrollbar-auto-thumb: $(get foreground);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --scrollbar-auto-track: transparent;" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --scrollbar-thin-thumb: $(get foreground);" >> ~/.config/vesktop/themes/shade-raid.theme.css
echo "  --scrollbar-thin-track: transparent;" >> ~/.config/vesktop/themes/shade-raid.theme.css

echo "  --border-radius: 0px;" >> ~/.config/vesktop/themes/shade-raid.theme.css
cat << 'EOF' >> ~/.config/vesktop/themes/shade-raid.theme.css
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
sudo "$DIR/sync-plymouth.sh" > /dev/null 2>&1 &
