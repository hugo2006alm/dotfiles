#!/bin/bash
set -e

echo "==> Setting up git..."
read -p "Git name: " git_name
read -p "Git email: " git_email
git config --global user.name "$git_name"
git config --global user.email "$git_email"
git config --global core.pager delta

echo "==> Setting fish as default shell..."
chsh -s /usr/bin/fish

echo "==> Setting up user directories..."
xdg-user-dirs-update

echo "==> Refreshing font cache..."
fc-cache -fv

echo "==> Cleaning up leftover bash files..."
rm -f ~/.bash_history ~/.bash_logout ~/.bash_profile ~/.bashrc

echo "==> Refreshing mirrors..."
sudo reflector --country PT,DE --latest 10 --sort rate --save /etc/pacman.d/mirrorlist

echo "==> Setting up mise..."
mise install node@lts
mise install python@latest

echo "==> Creating necessary directories"
mkdir -p ~/Pictures/Screenshots
mkdir -p ~/wallpapers/shade-raid
