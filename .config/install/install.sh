#!/bin/bash
set -e

echo "╔══════════════════════════════╗"
echo "║   Shade Raid — Arch Setup    ║"
echo "╚══════════════════════════════╝"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$DIR/../.." && pwd)"

# Ask the user if they want to configure GitHub SSH and CLI
read -r -p "Do you want to set up a new SSH key and authenticate GitHub CLI? (y/N): " setup_github
setup_flag=""
if [[ "$setup_github" =~ ^[Yy]$ ]]; then
    setup_flag="--github"
fi

echo "==> Optimizing pacman configuration..."
sudo sed -i '/^#\[multilib\]/s/^#//' /etc/pacman.conf
sudo sed -i '/^\[multilib\]/{n;s/^#//}' /etc/pacman.conf
sudo sed -i 's/^#Color$/Color/' /etc/pacman.conf
sudo sed -i 's/^#ParallelDownloads = 5$/ParallelDownloads = 5/' /etc/pacman.conf
sudo pacman -Sy --noconfirm

# Ensure yay is installed
if ! command -v yay &> /dev/null; then
    echo "==> Installing yay..."
    sudo pacman -S --needed --noconfirm git base-devel
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    cd /tmp/yay && makepkg -si --noconfirm
    cd "$PROJECT_ROOT" && rm -rf /tmp/yay
fi

# Ensure python and pip are installed
if ! command -v pip &> /dev/null; then
    echo "==> Installing python-pip..."
    sudo pacman -S --needed --noconfirm python python-pip
fi

# Install dotfiles_api CLI in editable mode
echo "==> Packaging dotfiles API CLI..."
cd "$PROJECT_ROOT"
pip install --break-system-packages -e .

# Run the Python setup service
echo "==> Starting setup execution..."
dotfiles setup $setup_flag

echo ""
echo "==> Done. Please reboot your system. greetd (login manager) will start automatically on TTY1."
