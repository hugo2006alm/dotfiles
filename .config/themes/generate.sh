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

# ── Hyprlock ──────────────────────────────
cat > ~/.config/hypr/hyprlock.conf << EOF
# Auto-generated from themes/$THEME/colors.toml — do not edit directly

background {
    monitor =
    color = rgb($(hex $lock_bg))
    blur_passes = 0
}

label {
    monitor =
    text = \$TIME
    color = rgb($(hex $lock_fg))
    font_size = 128
    font_family = Bebas Neue
    position = 0, 160
    halign = center
    valign = center
}

label {
    monitor =
    text = cmd[update:60000] date +'%A, %d %B %Y' | tr '[:lower:]' '[:upper:]'
    color = rgb($(hex $lock_fg))
    font_size = 14
    font_family = JetBrains Mono Nerd Font
    position = 0, 60
    halign = center
    valign = center
}

label {
    monitor =
    text = // LOCKED
    color = rgb($(hex $accent))
    font_size = 11
    font_family = JetBrains Mono Nerd Font
    position = 0, -40
    halign = center
    valign = center
}

input-field {
    monitor =
    size = 320, 50
    outline_thickness = 3
    dots_size = 0.25
    dots_spacing = 0.35
    dots_center = true
    outer_color = rgb($(hex $lock_input))
    inner_color = rgb($(hex $lock_bg))
    font_color = rgb($(hex $lock_fg))
    fade_on_empty = true
    placeholder_text = <span font_family="JetBrains Mono Nerd Font" font_size="13">PASSWORD</span>
    rounding = 0
    position = 0, -110
    halign = center
    valign = center
}
EOF

echo "Generated ~/.config/hypr/hyprlock.conf"

echo "Done — theme: $THEME"
