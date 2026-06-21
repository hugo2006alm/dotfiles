#!/bin/bash
set -e

if [ "$SETUP_GITHUB" = "y" ]; then
    echo "==> Setting up SSH key for GitHub..."
    read -r -p "GitHub email: " github_email
    ssh-keygen -t ed25519 -C "$github_email" -f ~/.ssh/github -N ""
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/github

    echo ""
    echo "==> Add this public key to GitHub (Settings → SSH keys):"
    echo ""
    cat ~/.ssh/github.pub
    echo ""
    read -r -p "Press Enter once you've added the key to GitHub..."
    ssh -T git@github.com || true
else
    echo "==> Skipping GitHub SSH setup."
fi

# Determine source repository directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOTFILES_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [ "$DOTFILES_DIR" != "$HOME/dotfiles" ]; then
    if [ -d "$HOME/dotfiles/.git" ]; then
        echo "==> ~/dotfiles already exists, skipping clone/copy..."
    else
        echo "==> Copying dotfiles repository to ~/dotfiles..."
        mkdir -p "$HOME"
        cp -r "$DOTFILES_DIR" "$HOME/dotfiles"
    fi
else
    echo "==> Already in ~/dotfiles, skipping clone/copy..."
fi

echo "==> Linking dotfiles with GNU Stow..."
cd "$HOME/dotfiles" || exit 1
stow . -t ~
git config --global push.autoSetupRemote true
