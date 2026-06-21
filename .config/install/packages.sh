#!/bin/bash
set -e

echo "==> Installing yay..."
if ! command -v yay &> /dev/null; then
    git clone https://aur.archlinux.org/yay.git /tmp/yay
    cd /tmp/yay && makepkg -si --noconfirm
    cd ~ && rm -rf /tmp/yay
fi

echo "==> Optimizing pacman configuration..."
sudo sed -i '/^#\[multilib\]/s/^#//' /etc/pacman.conf
sudo sed -i '/^\[multilib\]/{n;s/^#//}' /etc/pacman.conf
sudo sed -i 's/^#Color$/Color/' /etc/pacman.conf
sudo sed -i 's/^#ParallelDownloads = 5$/ParallelDownloads = 5/' /etc/pacman.conf
sudo pacman -Sy


# ── Pacman packages ───────────────────────
PACMAN_PKGS=(
    # Wayland / Hyprland
    hyprland
    xdg-desktop-portal-hyprland
    xdg-desktop-portal-gtk

    # Bar
    waybar
    sassc
    jq

    # Audio
    pipewire
    pipewire-pulse
    pipewire-alsa
    wireplumber

    # Network
    networkmanager
    network-manager-applet
    openvpn
    network-manager-openvpn

    # Bluetooth
    bluez
    bluez-utils

    # Wallpaper
    swww

    # Notifications
    mako

    # Launcher
    rofi-wayland

    # Terminal
    ghostty

    # Shell
    fish
    starship

    # Screenshot / screen
    grim
    slurp
    wl-clipboard
    cliphist
    pacman-contrib
    wf-recorder

    # Brightness
    brightnessctl

    # Media
    playerctl
    mpv
    imv
    pavucontrol

    # GTK / Qt theming
    nwg-look
    qt6ct
    qt5ct
    papirus-icon-theme


    # Polkit
    polkit-gnome

    # File manager
    nautilus
    tumbler
    ffmpegthumbnailer
    file-roller

    # System tools
    stow
    btop
    bc
    ufw
    reflector
    xdg-user-dirs
    openssh

    # Editors
    neovim
    lazygit
    github-cli

    # CLI tools
    bat
    eza
    fzf
    zoxide
    ripgrep
    fd
    git-delta

    # Python
    python-pip

    # Fonts
    ttf-jetbrains-mono-nerd
    ttf-liberation
    otf-monaspace

    # Misc
    unzip
    zip

    # Gaming (GPU — swap for nvidia if needed)
    mesa
    lib32-mesa
    vulkan-radeon
    lib32-vulkan-radeon
    libva-mesa-driver
    libva-utils
    gamescope

    # Steam
    steam

    # Keyring
    gnome-keyring
    seahorse
)

echo "==> Installing pacman packages..."
sudo pacman -S --needed --noconfirm "${PACMAN_PKGS[@]}"

# ── AUR packages ──────────────────────────
AUR_PKGS=(
    # Hyprland ecosystem
    hyprlock
    hypridle
    hyprsunset
    hyprpicker
    hyprshot

    # Login manager
    greetd
    greetd-regreet

    # Launcher & Backend Providers
    walker-bin
    elephant-all

    # OSD
    swayosd-git

    # Bluetooth TUI
    bluetui

    # Power menu
    wlogout

    # Runtime manager
    mise-bin

    # Cursors & Folders
    bibata-cursor-theme
    papirus-folders

    # Apps
    vesktop-bin
    heroic-games-launcher-bin
    bitwarden
    spotify
    spicetify-cli
    zen-browser-bin

    # Fonts
    ttf-iosevka-nerd
    otf-bebas-neue
)

echo "==> Installing AUR packages..."
yay -S --needed --noconfirm "${AUR_PKGS[@]}"
