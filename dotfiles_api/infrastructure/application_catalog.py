from dotfiles_api.infrastructure.reloadables.waybar import WaybarReloadable
from dotfiles_api.infrastructure.reloadables.swaync import SwayNCReloadable
from dotfiles_api.infrastructure.reloadables.user_service import UserServiceReloadable
from dotfiles_api.infrastructure.reloadables.gsettings import GsettingsReloadable
from dotfiles_api.infrastructure.reloadables.ghostty import GhosttyReloadable
from dotfiles_api.infrastructure.reloadables.walker import WalkerReloadable
from dotfiles_api.infrastructure.reloadables.wlogout import WlogoutReloadable
from dotfiles_api.infrastructure.reloadables.btop import BtopReloadable
from dotfiles_api.infrastructure.reloadables.hyprland import HyprlandReloadable
from dotfiles_api.infrastructure.reloadables.vesktop import VesktopReloadable
from dotfiles_api.infrastructure.reloadables.regreet import ReGreetReloadable
from dotfiles_api.infrastructure.generators.hypr import HyprlandGenerator
from dotfiles_api.infrastructure.generators.waybar import WaybarGenerator
from dotfiles_api.infrastructure.generators.ghostty import GhosttyGenerator
from dotfiles_api.infrastructure.generators.swaync import SwayncGenerator
from dotfiles_api.infrastructure.generators.swayosd import SwayosdGenerator
from dotfiles_api.infrastructure.generators.btop import BtopGenerator
from dotfiles_api.infrastructure.generators.walker import WalkerGenerator
from dotfiles_api.infrastructure.generators.wlogout import WlogoutGenerator
from dotfiles_api.infrastructure.generators.vesktop import VesktopGenerator
from dotfiles_api.infrastructure.generators.hyprlock import HyprlockGenerator
from dotfiles_api.infrastructure.generators.regreet import ReGreetGenerator
from dotfiles_api.infrastructure.generators.greetd import GreetdGenerator
from dotfiles_api.infrastructure.generators.gtk import GtkGenerator
from dotfiles_api.infrastructure.generators.plymouth import PlymouthGenerator
from dotfiles_api.domain.models.application_spec import ApplicationSpec
from dotfiles_api.domain.models.output_spec import OutputSpec
from dotfiles_api.domain.models.stylesheet_spec import StylesheetSpec


def _reload(cls):
    return lambda execution, env, store, loader: cls(exec_ctx=execution)


APPLICATIONS = (
    ApplicationSpec('hyprland', packages=('hyprland', 'hypridle', 'hyprsunset', 'hyprpicker', 'hyprshot', 'awww'), capabilities=('compositor',),
        generator=HyprlandGenerator,
        outputs=(
            OutputSpec('hyprland-colors', '.config/hypr/colors.lua'),
            OutputSpec('hyprland-style', '.config/hypr/style.lua'),
            OutputSpec('hyprland-colors-conf', '.config/hypr/colors.conf'),
            OutputSpec('hyprland-style-conf', '.config/hypr/style.conf'),
        ),
        reload_factory=_reload(HyprlandReloadable), reload_strategy="application",
    ),
    ApplicationSpec('waybar', packages=('waybar', 'sassc', 'jq'), capabilities=('status-bar',),
        user_unit="shade-raid-waybar.service",
        generator=WaybarGenerator,
        dependencies=("hyprland",),
        outputs=(
            OutputSpec('waybar-colors', '.config/waybar/colors.scss'),
            OutputSpec('waybar-variables', '.config/waybar/variables.scss'),
            OutputSpec('waybar-style', '.config/waybar/style.css'),
        ),
        stylesheets=(StylesheetSpec('.config/waybar/style.scss', 'waybar-style', ('waybar-colors', 'waybar-variables')),),
        reload_factory=_reload(WaybarReloadable), reload_strategy="systemd-user-reload",
    ),
    ApplicationSpec('ghostty', packages=('ghostty',), capabilities=('terminal',),
        generator=GhosttyGenerator,
        outputs=(
            OutputSpec('ghostty-colors', '.config/ghostty/colors.conf'),
        ),
        reload_factory=_reload(GhosttyReloadable), reload_strategy="application",
    ),
    ApplicationSpec('swaync', packages=('swaync', 'libnotify'), capabilities=('notification-center',),
        user_unit="shade-raid-swaync.service",
        generator=SwayncGenerator,
        dependencies=("hyprland",),
        outputs=(
            OutputSpec('swaync-config', '.config/swaync/config.json'),
            OutputSpec('swaync-style', '.config/swaync/style.css'),
        ),
        reload_factory=_reload(SwayNCReloadable), reload_strategy="application",
    ),
    ApplicationSpec('swayosd', packages=('swayosd',), capabilities=(),
        user_unit="shade-raid-swayosd.service",
        reload_factory=lambda execution, env, store, loader: UserServiceReloadable(execution, "swayosd", "shade-raid-swayosd.service"),
        reload_strategy="systemd-user-restart",
        generator=SwayosdGenerator,
        dependencies=("hyprland",),
        outputs=(
            OutputSpec('swayosd-colors', '.config/swayosd/_colors.scss'),
            OutputSpec('swayosd-style', '.config/swayosd/style.css'),
        ),
        stylesheets=(StylesheetSpec('.config/swayosd/style.scss', 'swayosd-style', ('swayosd-colors',)),),
    ),
    ApplicationSpec('btop', packages=('btop',), capabilities=(),
        generator=BtopGenerator,
        outputs=(
            OutputSpec('btop-theme', '.config/btop/themes/shade-raid.theme'),
            OutputSpec('btop-config', '.config/btop/btop.conf'),
        ),
        reload_factory=_reload(BtopReloadable), reload_strategy="application",
    ),
    ApplicationSpec('walker', packages=('walker-bin',), capabilities=('launcher',),
        user_unit="shade-raid-walker.service",
        package_sources=(('walker-bin', 'yay'),),
        generator=WalkerGenerator,
        dependencies=("hyprland", "elephant"),
        outputs=(
            OutputSpec('walker-colors', '.config/walker/themes/{theme_name}/_colors.scss'),
            OutputSpec('walker-config', '.config/walker/config.toml'),
            OutputSpec('walker-style', '.config/walker/themes/{theme_name}/style.css'),
        ),
        stylesheets=(StylesheetSpec('.config/walker/themes/style.scss', 'walker-style', ('walker-colors',)),),
        reload_factory=_reload(WalkerReloadable), reload_strategy="systemd-user-restart",
    ),
    ApplicationSpec('wlogout', packages=('wlogout',), capabilities=(),
        package_sources=(('wlogout', 'yay'),),
        generator=WlogoutGenerator,
        dependencies=("hyprland",),
        outputs=(
            OutputSpec('wlogout-colors', '.config/wlogout/_colors.scss'),
            OutputSpec('wlogout-style', '.config/wlogout/style.css'),
        ),
        stylesheets=(StylesheetSpec('.config/wlogout/style.scss', 'wlogout-style', ('wlogout-colors',)),),
        reload_factory=_reload(WlogoutReloadable), reload_strategy="application",
    ),
    ApplicationSpec('vesktop', packages=('vesktop-bin',), capabilities=(),
        profiles=('daily',),
        package_sources=(('vesktop-bin', 'yay'),),
        generator=VesktopGenerator,
        required=False,
        outputs=(
            OutputSpec('vesktop-theme', '.config/vesktop/themes/{theme_name}.theme.css'),
        ),
        reload_factory=lambda execution, env, store, loader: VesktopReloadable(execution, store), reload_strategy="application",
    ),
    ApplicationSpec('hyprlock', packages=('hyprlock',), capabilities=(),
        generator=HyprlockGenerator,
        outputs=(
            OutputSpec('hyprlock-config', '.config/hypr/hyprlock.conf'),
        ),
    ),
    ApplicationSpec('regreet', packages=(), capabilities=(),
        generator=ReGreetGenerator,
        outputs=(
            OutputSpec('regreet-style', '.config/greetd/regreet.css'),
        ),
        reload_factory=lambda execution, env, store, loader: ReGreetReloadable(execution, env), reload_strategy="application",
    ),
    ApplicationSpec('greetd', packages=('greetd', 'greetd-regreet'), capabilities=('login',),
        generator=GreetdGenerator,
        outputs=(
            OutputSpec('greetd-config', '.config/greetd/regreet.toml'),
        ),
    ),
    ApplicationSpec('gtk', packages=('nwg-look', 'qt6ct', 'qt5ct', 'papirus-icon-theme', 'bibata-cursor-theme', 'papirus-folders'), capabilities=('theming',),
        profiles=('appearance',),
        package_sources=(('bibata-cursor-theme', 'yay'), ('papirus-folders', 'yay')),
        generator=GtkGenerator,
        outputs=(
            OutputSpec('gtk3-settings', '.config/gtk-3.0/settings.ini'),
            OutputSpec('gtk4-settings', '.config/gtk-4.0/settings.ini'),
            OutputSpec('gtk3-css', '.config/gtk-3.0/gtk.css'),
            OutputSpec('gtk4-css', '.config/gtk-4.0/gtk.css'),
        ),
        reload_factory=lambda execution, env, store, loader: GsettingsReloadable(execution, store, loader), reload_strategy="application",
    ),
    ApplicationSpec('plymouth', packages=('plymouth',), capabilities=(),
        generator=PlymouthGenerator,
        outputs=(
            OutputSpec('plymouth-theme', 'generated/plymouth/shade-raid.script', "state"),
        ),
    ),
    ApplicationSpec('audio', packages=('pipewire', 'pipewire-pulse', 'pipewire-alsa', 'wireplumber', 'pavucontrol'), capabilities=('audio',),
    ),
    ApplicationSpec('network', packages=('networkmanager', 'network-manager-applet', 'openvpn', 'networkmanager-openvpn'), capabilities=('network',),
    ),
    ApplicationSpec('bluetooth', packages=('bluez', 'bluez-utils', 'bluetui'), capabilities=('bluetooth',),
    ),
    ApplicationSpec('shell', packages=('fish', 'starship', 'zoxide', 'stow', 'bat', 'eza', 'fzf', 'ripgrep', 'fd', 'git-delta'), capabilities=('shell',),
        profiles=('core',),
    ),
    ApplicationSpec('screenshot', packages=('grim', 'slurp', 'wl-clipboard', 'cliphist', 'pacman-contrib', 'wf-recorder'), capabilities=('screenshot',),
    ),
    ApplicationSpec('brightness', packages=('brightnessctl',), capabilities=('brightness',),
    ),
    ApplicationSpec('media', packages=('playerctl', 'mpv', 'imv'), capabilities=('media',),
    ),
    ApplicationSpec('polkit', packages=('polkit-gnome',), capabilities=('polkit',),
    ),
    ApplicationSpec('filemanager', packages=('nautilus', 'tumbler', 'ffmpegthumbnailer', 'file-roller'), capabilities=('file-manager',),
    ),
    ApplicationSpec('system', packages=('stow', 'bc', 'ufw', 'rate-mirrors', 'xdg-user-dirs', 'openssh', 'imagemagick', 'unzip', 'zip', 'curl', 'mise'), capabilities=('system',),
        profiles=('core',),
    ),
    ApplicationSpec('editors', packages=('neovim', 'lazygit', 'github-cli'), capabilities=('editors',),
        profiles=('desktop', 'dev'),
    ),
    ApplicationSpec('fonts', packages=('ttf-jetbrains-mono-nerd', 'ttf-liberation', 'otf-monaspace', 'ttf-iosevka-nerd', 'ttf-space-mono-nerd', 'noto-fonts-emoji', 'otf-bebas-neue-git'), capabilities=('fonts',),
        profiles=('appearance',),
        package_sources=(('otf-bebas-neue-git', 'yay'),),
    ),
    ApplicationSpec('keyring', packages=('gnome-keyring', 'seahorse'), capabilities=('keyring',),
    ),
    ApplicationSpec('elephant', packages=('elephant-all',), package_sources=(("elephant-all", "yay"),),
        user_unit="shade-raid-elephant.service", dependencies=("hyprland",),
    ),
    ApplicationSpec('portal', packages=('xdg-desktop-portal', 'xdg-desktop-portal-hyprland', 'xdg-desktop-portal-gtk'),
        capabilities=(), dependencies=("hyprland",),
    ),
    ApplicationSpec("core-tools", packages=("git", "python"), profiles=("core",)),
    ApplicationSpec("browser", packages=("zen-browser-bin",), package_sources=(("zen-browser-bin", "yay"),),
        profiles=("daily",), required=False),
    ApplicationSpec("password-manager", packages=("bitwarden",), profiles=("daily",), required=False),
    ApplicationSpec("development", packages=("uv", "docker"), profiles=("dev",), required=False),
    ApplicationSpec("gaming", packages=("steam",), profiles=("gaming",), required=False),
    ApplicationSpec("ai", packages=("ollama",), profiles=("ai",), required=False),
)
