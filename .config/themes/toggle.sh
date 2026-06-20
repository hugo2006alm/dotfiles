#!/bin/bash

current=$(cat ~/.config/themes/current)

if [[ "$current" == *-dark ]]; then
    next="${current%-dark}"
    scheme="prefer-light"
    gtk_theme="Adwaita"
    icon_theme="Papirus-Light"
else
    next="${current}-dark"
    scheme="prefer-dark"
    gtk_theme="Adwaita-dark"
    icon_theme="Papirus-Dark"
fi

~/.config/themes/apply.sh "$next"
gsettings set org.gnome.desktop.interface color-scheme "$scheme"
gsettings set org.gnome.desktop.interface gtk-theme "$gtk_theme"
gsettings set org.gnome.desktop.interface icon-theme "$icon_theme"

