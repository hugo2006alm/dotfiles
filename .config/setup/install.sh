#!/bin/bash
# Shade Raid — Arch Linux Hyprland Setup
# Run this on a fresh Arch install with base-devel and git
set -e  # stop on any error

echo "==> Installing yay..."
if ! command -v yay &> /dev/null; then
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    cd /tmp/yay && makepkg -si --noconfirm
    cd ~ && rm -rf /tmp/yay
fi

echo "==> Installing pacman packages..."
sudo pacman -S --needed --noconfirm \
    hyprland xdg-desktop-portal-hyprland \
    waybar \
    pipewire pipewire-pulse wireplumber \
    networkmanager \
    swww \
    mako \
    rofi-wayland \
    ghostty \
    fish \
    starship \
    grim slurp wl-clipboard cliphist \
    brightnessctl \
    playerctl \
    nwg-look \
    ttf-jetbrains-mono-nerd \
    polkit-gnome \
    nautilus \
    btop \
    neovim \
    pavucontrol \
    mpv \
    bluez bluez-utils \
    xdg-user-dirs \
    bat eza fzf zoxide ripgrep fd \
    imv \
    openssh \
    ttf-liberation \
    otf-monaspace

echo "==> Installing AUR packages..."
yay -S --needed --noconfirm \
    walker-bin \
    swayosd-git \
    bluetui \
    hyprlock \
    hypridle \
    hyprpicker \
    bibata-cursor-theme \
    phinger-cursors \
    capitaine-cursors \
    ttf-iosevka-nerd \
    otf-bebas-neue \
    zen-browser-bin

echo "==> Cloning dotfiles..."
git clone --bare https://github.com/hugo2006alm/dotfiles.git ~/.dotfiles

echo "==> Checking out dotfiles..."
git --git-dir=$HOME/.dotfiles --work-tree=$HOME checkout 2>&1 | grep -E "\s+\." | awk '{print $1}' | xargs -I{} mv {} {}.bak
git --git-dir=$HOME/.dotfiles --work-tree=$HOME checkout
git --git-dir=$HOME/.dotfiles --work-tree=$HOME config status.showUntrackedFiles no

echo "==> Generating Hyprland color config..."
bash ~/.config/theme/generate-hypr.sh

echo "==> Setting fish as default shell..."
chsh -s /usr/bin/fish

echo "==> Setting up user directories..."
xdg-user-dirs-update

echo "==> Enabling services..."
sudo systemctl enable NetworkManager
sudo systemctl enable bluetooth
sudo systemctl enable sshd
systemctl --user enable --now pipewire pipewire-pulse wireplumber

echo "==> Done. Log out and back in, then run Hyprland."
