#!/bin/bash
set -e

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
ssh -T git@github.com || true

echo "==> Cloning dotfiles..."
git clone git@github.com:hugo2006alm/dotfiles.git ~/dotfiles

echo "==> Linking dotfiles with GNU Stow..."
cd ~/dotfiles
stow . -t ~
git config --global push.autoSetupRemote true
