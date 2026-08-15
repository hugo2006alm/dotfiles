from dotfiles_api.application.hardware import COMMON_GRAPHICS_PACKAGES
from dotfiles_api.domain.models.feature import Feature
from dotfiles_api.domain.models.profile import Profile


def build_desktop_profile(
    optional_packages: list[str] | None = None,
    graphics_packages: list[str] | None = None,
) -> Profile:
    selected_graphics = list(graphics_packages or COMMON_GRAPHICS_PACKAGES)

    features = [
        Feature(name="compositor", packages=["hyprland", "xdg-desktop-portal-hyprland", "xdg-desktop-portal-gtk", "hyprlock", "hypridle", "hyprsunset", "hyprpicker", "hyprshot", "awww"], capabilities=["compositor"]),
        Feature(name="statusbar", packages=["waybar", "sassc", "jq"], capabilities=["status-bar"]),
        Feature(name="audio", packages=["pipewire", "pipewire-pulse", "pipewire-alsa", "wireplumber", "pavucontrol"], capabilities=["audio"]),
        Feature(name="network", packages=["networkmanager", "network-manager-applet", "openvpn", "networkmanager-openvpn"], capabilities=["network"]),
        Feature(name="bluetooth", packages=["bluez", "bluez-utils", "bluetui"], capabilities=["bluetooth"]),
        Feature(name="notifications", packages=["swaync", "libnotify"], capabilities=["notification-center"]),
        Feature(name="launcher", packages=["walker-bin", "elephant-all"], capabilities=["launcher"]),
        Feature(name="terminal", packages=["ghostty"], capabilities=["terminal"]),
        Feature(name="shell", packages=["fish", "starship", "zoxide", "stow", "bat", "eza", "fzf", "ripgrep", "fd", "git-delta"], capabilities=["shell"]),
        Feature(name="screenshot", packages=["grim", "slurp", "wl-clipboard", "cliphist", "pacman-contrib", "wf-recorder"], capabilities=["screenshot"]),
        Feature(name="brightness", packages=["brightnessctl"], capabilities=["brightness"]),
        Feature(name="media", packages=["playerctl", "mpv", "imv"], capabilities=["media"]),
        Feature(name="theming", packages=["nwg-look", "qt6ct", "qt5ct", "papirus-icon-theme", "bibata-cursor-theme", "papirus-folders", "swayosd"], capabilities=["theming"]),
        Feature(name="polkit", packages=["polkit-gnome"], capabilities=["polkit"]),
        Feature(name="filemanager", packages=["nautilus", "tumbler", "ffmpegthumbnailer", "file-roller"], capabilities=["file-manager"]),
        Feature(name="system", packages=["stow", "btop", "bc", "ufw", "rate-mirrors", "xdg-user-dirs", "openssh", "imagemagick", "unzip", "zip", "curl", "mise", "plymouth", "wlogout"], capabilities=["system"]),
        Feature(name="login", packages=["greetd", "greetd-regreet"], capabilities=["login"]),
        Feature(name="editors", packages=["neovim", "lazygit", "github-cli"], capabilities=["editors"]),
        Feature(name="fonts", packages=["ttf-jetbrains-mono-nerd", "ttf-liberation", "otf-monaspace", "ttf-iosevka-nerd", "ttf-space-mono-nerd", "noto-fonts-emoji", "otf-bebas-neue-git"], capabilities=["fonts"]),
        Feature(name="graphics", packages=selected_graphics, capabilities=["graphics"]),
        Feature(name="keyring", packages=["gnome-keyring", "seahorse"], capabilities=["keyring"]),
    ]

    selected = list(optional_packages or [])
    if selected:
        features.append(Feature(name="optional", packages=selected, capabilities=[]))

    return Profile(name="desktop", features=features)
