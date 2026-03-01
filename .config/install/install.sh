#!/bin/bash
set -e

echo "╔══════════════════════════════╗"
echo "║   Shade Raid — Arch Setup    ║"
echo "╚══════════════════════════════╝"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

bash "$DIR/packages.sh"
bash "$DIR/dotfiles.sh"
bash "$DIR/services.sh"
bash "$DIR/user.sh"
bash "$DIR/theme.sh"
bash "$DIR/extras.sh"

echo ""
echo "==> Done. Log out and back in, then start Hyprland."
