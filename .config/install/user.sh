#!/bin/bash
set -e

# 1. Setting up git
EXISTING_NAME=$(git config --global user.name || true)
EXISTING_EMAIL=$(git config --global user.email || true)

if [ -n "$EXISTING_NAME" ] && [ -n "$EXISTING_EMAIL" ]; then
    echo "==> Git is already configured (Name: $EXISTING_NAME, Email: $EXISTING_EMAIL). Skipping git config..."
else
    echo "==> Setting up git..."
    read -r -p "Git name [Press Enter to skip]: " git_name
    read -r -p "Git email [Press Enter to skip]: " git_email
    [ -n "$git_name" ] && git config --global user.name "$git_name"
    [ -n "$git_email" ] && git config --global user.email "$git_email"
fi
git config --global core.pager delta

# 2. Shell
echo "==> Setting fish as default shell..."
chsh -s /usr/bin/fish

# 3. User directories
echo "==> Setting up user directories..."
xdg-user-dirs-update

# 4. Font Cache
echo "==> Refreshing font cache..."
fc-cache -fv

# 5. Clean bash leftovers
echo "==> Cleaning up leftover bash files..."
rm -f ~/.bash_history ~/.bash_logout ~/.bash_profile ~/.bashrc

# 6. Reflector
echo "==> Refreshing mirrors..."
sudo reflector --latest 20 --protocol https --sort rate --save /etc/pacman.d/mirrorlist

# 7. mise
echo "==> Setting up mise..."
mise install python@latest

# 8. Creating directories dynamically
PICTURES_DIR="$(xdg-user-dir PICTURES)"
VIDEOS_DIR="$(xdg-user-dir VIDEOS)"
DESKTOP_DIR="$(xdg-user-dir DESKTOP)"
DOWNLOAD_DIR="$(xdg-user-dir DOWNLOAD)"
DOCUMENTS_DIR="$(xdg-user-dir DOCUMENTS)"
MUSIC_DIR="$(xdg-user-dir MUSIC)"

echo "==> Creating necessary directories..."
mkdir -p "${PICTURES_DIR:-$HOME/Pictures}/Screenshots"
mkdir -p "${VIDEOS_DIR:-$HOME/Videos}/Recordings"
mkdir -p "$HOME/wallpapers/shade-raid"

# 9. Generate GTK bookmarks dynamically based on user's actual locale/paths
echo "==> Configuring GTK bookmarks..."
mkdir -p "$HOME/.config/gtk-3.0"
cat > "$HOME/.config/gtk-3.0/bookmarks" << EOF
file://${DOWNLOAD_DIR:-$HOME/Downloads} Downloads
file://${DOCUMENTS_DIR:-$HOME/Documents} Documents
file://${PICTURES_DIR:-$HOME/Pictures} Pictures
file://${MUSIC_DIR:-$HOME/Music} Music
file://${VIDEOS_DIR:-$HOME/Videos} Videos
file://${DESKTOP_DIR:-$HOME/Desktop} Desktop
EOF

# 10. Fisher
echo "==> Installing Fisher and fish plugins..."
fish -c "curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fisher && fisher update"

# 11. GitHub CLI login
if [ "$SETUP_GITHUB" = "y" ]; then
    echo "==> Authenticating GitHub CLI..."
    gh auth login
else
    echo "==> Skipping GitHub CLI authentication. You can run 'gh auth login' manually later."
fi

# 12. Create personal autostart config from template if it doesn't exist
if [ ! -f "$HOME/.config/hypr/autostart-personal.lua" ] && [ -f "$HOME/.config/hypr/autostart-personal.lua.example" ]; then
    echo "==> Creating default personal autostart config..."
    cp "$HOME/.config/hypr/autostart-personal.lua.example" "$HOME/.config/hypr/autostart-personal.lua"
fi
