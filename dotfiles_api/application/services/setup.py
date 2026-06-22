from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.domain.contracts.linker import Linker
from dotfiles_api.application.services.theme import ThemeService
from dotfiles_api.application.services.services import ServicesSetupService
from dotfiles_api.application.services.user import UserSetupService
from dotfiles_api.application.services.extras import ExtrasSetupService
from dotfiles_api.domain.models.feature import Feature
from dotfiles_api.domain.models.profile import Profile

class SetupService:
    def __init__(
        self,
        env: EnvironmentContext,
        exec_ctx: ExecutionContext,
        install_service: InstallService,
        linker: Linker,
        theme_service: ThemeService,
        services_service: ServicesSetupService,
        user_service: UserSetupService,
        extras_service: ExtrasSetupService
    ) -> None:
        self._env = env
        self._exec = exec_ctx
        self._install_service = install_service
        self._linker = linker
        self._theme_service = theme_service
        self._services = services_service
        self._user = user_service
        self._extras = extras_service

    def run_setup(self, setup_github: bool = False) -> None:
        features = [
            Feature(name="compositor", packages=["hyprland", "xdg-desktop-portal-hyprland", "xdg-desktop-portal-gtk", "hyprlock", "hypridle", "hyprsunset", "hyprpicker", "hyprshot", "awww"], capabilities=["compositor"]),
            Feature(name="statusbar", packages=["waybar", "sassc", "jq"], capabilities=["status-bar"]),
            Feature(name="audio", packages=["pipewire", "pipewire-pulse", "pipewire-alsa", "wireplumber", "pavucontrol"], capabilities=["audio"]),
            Feature(name="network", packages=["networkmanager", "network-manager-applet", "openvpn", "network-manager-openvpn"], capabilities=["network"]),
            Feature(name="bluetooth", packages=["bluez", "bluez-utils", "bluetui"], capabilities=["bluetooth"]),
            Feature(name="notifications", packages=["swaync", "libnotify"], capabilities=["notification-center"]),
            Feature(name="launcher", packages=["walker-bin", "elephant-all", "rofi-wayland"], capabilities=["launcher"]),
            Feature(name="terminal", packages=["ghostty"], capabilities=["terminal"]),
            Feature(name="shell", packages=["fish", "starship", "zoxide", "stow", "bat", "eza", "fzf", "ripgrep", "fd", "git-delta"], capabilities=["shell"]),
            Feature(name="screenshot", packages=["grim", "slurp", "wl-clipboard", "cliphist", "pacman-contrib", "wf-recorder"], capabilities=["screenshot"]),
            Feature(name="brightness", packages=["brightnessctl"], capabilities=["brightness"]),
            Feature(name="media", packages=["playerctl", "mpv", "imv", "spotify", "spicetify-cli"], capabilities=["media"]),
            Feature(name="theming", packages=["nwg-look", "qt6ct", "qt5ct", "papirus-icon-theme", "bibata-cursor-theme", "papirus-folders", "swayosd-git"], capabilities=["theming"]),
            Feature(name="polkit", packages=["polkit-gnome"], capabilities=["polkit"]),
            Feature(name="filemanager", packages=["nautilus", "tumbler", "ffmpegthumbnailer", "file-roller"], capabilities=["file-manager"]),
            Feature(name="system", packages=["stow", "btop", "bc", "ufw", "reflector", "xdg-user-dirs", "openssh", "imagemagick", "unzip", "zip", "mise-bin"], capabilities=["system"]),
            Feature(name="login", packages=["greetd", "greetd-regreet"], capabilities=["login"]),
            Feature(name="editors", packages=["neovim", "lazygit", "github-cli"], capabilities=["editors"]),
            Feature(name="fonts", packages=["ttf-jetbrains-mono-nerd", "ttf-liberation", "otf-monaspace", "ttf-iosevka-nerd", "otf-bebas-neue"], capabilities=["fonts"]),
            Feature(name="gaming", packages=["mesa", "lib32-mesa", "vulkan-radeon", "lib32-vulkan-radeon", "libva-mesa-driver", "libva-utils", "gamescope", "steam", "heroic-games-launcher-bin"], capabilities=["gaming"]),
            Feature(name="apps", packages=["vesktop-bin", "bitwarden", "zen-browser-bin"], capabilities=["apps"]),
            Feature(name="keyring", packages=["gnome-keyring", "seahorse"], capabilities=["keyring"]),
        ]
        desktop_profile = Profile(name="desktop", features=features)

        self._install_service.install_profile(desktop_profile)
        self._linker.link(self._env.dotfiles_dir, self._env.home_dir)
        self._services.setup_services()
        self._user.setup_user(setup_github=setup_github)
        self._theme_service.apply_theme("shade-raid")
        self._extras.setup_extras()
