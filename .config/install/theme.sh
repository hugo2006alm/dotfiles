#!/bin/bash
set -e

echo "==> Generating and applying theme..."
python -m dotfiles_api.presentation.cli configure --theme shade-raid
echo "==> Theme generated. Will apply on first Hyprland launch."
