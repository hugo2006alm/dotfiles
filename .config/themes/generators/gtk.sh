#!/bin/bash

THEME="$1"
TOML="$HOME/.config/themes/$THEME/colors.toml"
STYLE="$HOME/.config/themes/style.toml"

get()  { grep "^$1 " "$TOML"  | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }
gets() { grep "^$1 " "$STYLE" | head -1 | sed 's/.*= *"\(.*\)"/\1/'; }

# Determine dark/light settings
IS_DARK=false
[[ "$THEME" == *"-dark"* ]] && IS_DARK=true

if $IS_DARK; then
    gtk_theme="Adwaita-dark"
    icon_theme="Papirus-Dark"
else
    gtk_theme="Adwaita"
    icon_theme="Papirus-Light"
fi

cursor_theme=$(gets cursor_theme)
cursor_size=$(gets cursor_size)
font_mono=$(gets font_mono)
font_size_md=$(gets font_size_md)

# Write to gtk-3.0 settings.ini
mkdir -p ~/.config/gtk-3.0
cat > ~/.config/gtk-3.0/settings.ini << EOF
[Settings]
gtk-theme-name = $gtk_theme
gtk-icon-theme-name = $icon_theme
gtk-font-name = $font_mono $font_size_md
gtk-cursor-theme-name = $cursor_theme
gtk-cursor-theme-size = $cursor_size
EOF

# Write to gtk-4.0 settings.ini
mkdir -p ~/.config/gtk-4.0
cat > ~/.config/gtk-4.0/settings.ini << EOF
[Settings]
gtk-theme-name = $gtk_theme
gtk-icon-theme-name = $icon_theme
gtk-font-name = $font_mono $font_size_md
gtk-cursor-theme-name = $cursor_theme
gtk-cursor-theme-size = $cursor_size
EOF

# Determine Papirus folder color based on theme settings
folder_color=$(get papirus_folder_color)
if [ -z "$folder_color" ]; then
    # Fallback to mapping by accent color
    accent=$(get accent)
    if [[ "$accent" == "#D94F2B" ]] || [[ "$accent" == "#E8623E" ]] || [[ "$accent" == "#B33E20" ]]; then
        folder_color="orange"
    elif [[ "$accent" == "#6B8E23" ]] || [[ "$accent" == "#556B2F" ]]; then
        folder_color="green"
    else
        folder_color="grey" # safe default fallback
    fi
fi

# Run papirus-folders locally if installed
if command -v papirus-folders &>/dev/null; then
    papirus-folders -C "$folder_color" >/dev/null 2>&1 || true
fi

echo "Generated GTK settings.ini for $THEME (folders: $folder_color)"
