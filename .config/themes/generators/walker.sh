#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

# Load colors and styles in a single pass (0ms overhead)
declare -A colors
while IFS= read -r line; do
  if [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*\"([^\"]+)\" ]]; then
    colors["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  elif [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*([0-9.]+) ]]; then
    colors["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  fi
done < "$TOML"

declare -A style
while IFS= read -r line; do
  if [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*\"([^\"]+)\" ]]; then
    style["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  elif [[ "$line" =~ ^[[:space:]]*([a-zA-Z0-9_]+)[[:space:]]*=[[:space:]]*([0-9.]+) ]]; then
    style["${BASH_REMATCH[1]}"]="${BASH_REMATCH[2]}"
  fi
done < "$STYLE"

background="${colors[background]}"
background2="${colors[background2]}"
foreground="${colors[foreground]}"
foreground2="${colors[foreground2]}"
border="${colors[border]}"
accent="${colors[accent]}"
inactive="${colors[inactive]}"
font_mono="${style[font_mono]}"
font_size_sm="${style[font_size_sm]}"
font_size_md="${style[font_size_md]}"

mkdir -p ~/.config/walker/themes/$THEME

cat > ~/.config/walker/themes/$THEME/_colors.scss << EOF
// Auto-generated from themes/$THEME/colors.toml — do not edit directly
\$background:   $background;
\$background2:  $background2;
\$foreground:   $foreground;
\$foreground2:  $foreground2;
\$border:       $border;
\$accent:       $accent;
\$inactive:     $inactive;
\$font_mono:    "$font_mono";
\$font_size_sm: ${font_size_sm}px;
\$font_size_md: ${font_size_md}px;
EOF

echo "Generated ~/.config/walker/themes/$THEME/_colors.scss"

cp ~/.config/walker/themes/$THEME/_colors.scss ~/.config/walker/themes/_colors.scss

cd ~/.config/walker/themes
sassc -I $THEME \
  style.scss \
  $THEME/style.css
echo "Compiled walker style.scss → style.css"

# Generate ~/.config/walker/config.toml based on the system default config.toml
CONF_SOURCE="/etc/xdg/walker/config.toml"
CONF_DEST="$HOME/.config/walker/config.toml"
if [ -f "$CONF_SOURCE" ]; then
    cp "$CONF_SOURCE" "$CONF_DEST"
    # Replace theme
    sed -i "s/^theme[[:space:]]*=.*/theme = \"$THEME\"/" "$CONF_DEST"
    # Append custom provider overrides
    cat >> "$CONF_DEST" << 'EOF'

[providers.symbols]
show_initial_entries = true
EOF
else
    # Fallback to a minimal working config if system config is not found
    cat > "$CONF_DEST" << EOF
theme = "$THEME"

[search]
placeholder = "Search..."

[providers]
default = ["desktopapplications", "calc", "websearch"]
empty = ["desktopapplications"]

[[providers.prefixes]]
prefix = "."
provider = "symbols"

[[providers.prefixes]]
prefix = "="
provider = "calc"

[[providers.prefixes]]
prefix = ":"
provider = "clipboard"

[providers.symbols]
show_initial_entries = true
EOF
fi

echo "Generated ~/.config/walker/config.toml based on $CONF_SOURCE"

