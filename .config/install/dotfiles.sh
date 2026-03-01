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
git clone --bare git@github.com:hugo2006alm/dotfiles.git ~/.dotfiles

echo "==> Checking out dotfiles..."
git --git-dir=$HOME/.dotfiles --work-tree=$HOME checkout 2>&1 \
    | grep -E "\s+\." | awk '{print $1}' \
    | xargs -I{} mv {} {}.bak || true
git --git-dir=$HOME/.dotfiles --work-tree=$HOME checkout
git --git-dir=$HOME/.dotfiles --work-tree=$HOME config status.showUntrackedFiles no
git --git-dir=$HOME/.dotfiles --work-tree=$HOME config --global push.autoSetupRemote true
git --git-dir=$HOME/.dotfiles --work-tree=$HOME remote set-url origin git@github.com:hugo2006alm/dotfiles.git
