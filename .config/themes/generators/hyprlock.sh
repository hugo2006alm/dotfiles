#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"

get()  { grep "^$1 " "$TOML"  | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
hex()  { echo "${1#\#}"; }

# Colors
lock_bg=$(get lock_bg)
lock_fg=$(get lock_fg)
lock_input=$(get lock_input)
accent=$(get accent)

# Fallbacks if missing
[ -z "$lock_bg" ] && lock_bg="#000000"
[ -z "$lock_fg" ] && lock_fg="#FFFFFF"
[ -z "$lock_input" ] && lock_input="#FFFFFF"
[ -z "$accent" ] && accent="#FF0000"

cat > ~/.config/hypr/hyprlock.conf << CONF
# Auto-generated from themes/$THEME/colors.toml — do not edit directly

background {
    monitor =
    color = rgb($(hex "$lock_bg"))
    blur_passes = 0
}

label {
    monitor =
    text = \$TIME
    color = rgb($(hex "$lock_fg"))
    font_size = 128
    font_family = Bebas Neue
    position = 0, 160
    halign = center
    valign = center
}

label {
    monitor =
    text = cmd[update:60000] date +'%A, %d %B %Y' | tr '[:lower:]' '[:upper:]'
    color = rgb($(hex "$lock_fg"))
    font_size = 14
    font_family = JetBrains Mono Nerd Font
    position = 0, 60
    halign = center
    valign = center
}

label {
    monitor =
    text = // LOCKED
    color = rgb($(hex "$accent"))
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
    dots_center = false
    outer_color = rgb($(hex "$lock_input"))
    inner_color = rgb($(hex "$lock_bg"))
    font_color = rgb($(hex "$lock_fg"))
    fade_on_empty = true
    placeholder_text = <span font_family="JetBrains Mono Nerd Font" font_size="13">PASSWORD</span>
    rounding = 0
    position = 0, -110
    halign = center
    valign = center
}
CONF

echo "Generated ~/.config/hypr/hyprlock.conf"
