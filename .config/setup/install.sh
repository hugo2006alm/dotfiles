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
    vesktop-bin \
    heroic-games-launcher-bin \
    antigravity \
    ttf-iosevka-nerd \
    otf-bebas-neue \
    zen-browser-bin

echo "==> Setting up SSH key for GitHub..."
read -p "GitHub email: " github_email
ssh-keygen -t ed25519 -C "$github_email" -f ~/.ssh/github -N ""
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github
echo ""
echo "==> Add this public key to GitHub (Settings → SSH keys):"
echo ""
cat ~/.ssh/github.pub
echo ""
read -p "Press Enter once you've added the key to GitHub..."

echo "==> Cloning dotfiles..."
git clone --bare git@github.com:hugo2006alm/dotfiles.git ~/.dotfiles

echo "==> Checking out dotfiles..."
git --git-dir=$HOME/.dotfiles --work-tree=$HOME checkout 2>&1 | grep -E "\s+\." | awk '{print $1}' | xargs -I{} mv {} {}.bak
git --git-dir=$HOME/.dotfiles --work-tree=$HOME checkout
git --git-dir=$HOME/.dotfiles --work-tree=$HOME config status.showUntrackedFiles no
git --git-dir=$HOME/.dotfiles --work-tree=$HOME config --global push.autoSetupRemote true
git --git-dir=$HOME/.dotfiles --work-tree=$HOME remote set-url origin git@github.com:hugo2006alm/dotfiles.git

echo "==> Setting up git..."
read -p "Git name: " git_name
read -p "Git email: " git_email
git config --global user.name "$git_name"
git config --global user.email "$git_email"

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
