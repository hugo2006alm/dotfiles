#!/bin/bash

current=$(cat ~/.config/themes/current)

if [[ "$current" == *-dark ]]; then
    next="${current%-dark}"
    scheme="prefer-light"
else
    next="${current}-dark"
    scheme="prefer-dark"
fi

~/.config/themes/apply.sh "$next"
gsettings set org.gnome.desktop.interface color-scheme "$scheme"
