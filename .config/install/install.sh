#!/bin/bash
set -e

echo "╔══════════════════════════════╗"
echo "║   Shade Raid — Arch Setup    ║"
echo "╚══════════════════════════════╝"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ask the user if they want to configure GitHub SSH and CLI
read -p "Do you want to set up a new SSH key and authenticate GitHub CLI? (y/N): " setup_github
if [[ "$setup_github" =~ ^[Yy]$ ]]; then
    export SETUP_GITHUB="y"
else
    export SETUP_GITHUB="n"
fi

bash "$DIR/packages.sh"
bash "$DIR/dotfiles.sh"
bash "$DIR/services.sh"
bash "$DIR/user.sh"
bash "$DIR/theme.sh"
bash "$DIR/extras.sh"

echo ""
echo "==> Done. Please reboot your system. greetd (login manager) will start automatically on TTY1."
