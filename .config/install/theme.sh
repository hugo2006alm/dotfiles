#!/bin/bash
set -e

echo "==> Generating and applying theme..."
bash ~/.config/themes/generate.sh shade-raid
echo "shade-raid" > ~/.config/themes/current
echo "==> Theme generated. Will apply on first Hyprland launch."
