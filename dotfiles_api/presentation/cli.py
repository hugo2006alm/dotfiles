import argparse
import sys
import os
import getpass
from pathlib import Path

from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
from dotfiles_api.infrastructure.file_store import FileThemeStore
from dotfiles_api.infrastructure.linker import StowLinker
from dotfiles_api.infrastructure.package_sources.pacman import PacmanSource
from dotfiles_api.infrastructure.package_sources.yay import YaySource

# Reloadables
from dotfiles_api.infrastructure.reloadables.waybar import WaybarReloadable
from dotfiles_api.infrastructure.reloadables.swaync import SwayNCReloadable
from dotfiles_api.infrastructure.reloadables.portal import XDGPortalReloadable
from dotfiles_api.infrastructure.reloadables.gsettings import GsettingsReloadable
from dotfiles_api.infrastructure.reloadables.ghostty import GhosttyReloadable
from dotfiles_api.infrastructure.reloadables.walker import WalkerReloadable
from dotfiles_api.infrastructure.reloadables.wlogout import WlogoutReloadable
from dotfiles_api.infrastructure.reloadables.btop import BtopReloadable
from dotfiles_api.infrastructure.reloadables.hyprland import HyprlandReloadable

# Generators
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

from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.services.theme import ThemeService
from dotfiles_api.application.services.reload import ReloadService
from dotfiles_api.application.facade import DotfilesFacade
from dotfiles_api.domain.models.feature import Feature
from dotfiles_api.domain.models.profile import Profile
from dotfiles_api.domain.events import EventBus, ThemeChangedEvent, ConfigGeneratedEvent

# Setup services
from dotfiles_api.application.services.services import ServicesSetupService
from dotfiles_api.application.services.user import UserSetupService
from dotfiles_api.application.services.extras import ExtrasSetupService
from dotfiles_api.application.services.setup import SetupService

# Actions
from dotfiles_api.application.services.action import ActionService
from dotfiles_api.infrastructure.actions.command import CommandAction
from dotfiles_api.infrastructure.actions.screenshot import ScreenshotAction
from dotfiles_api.infrastructure.actions.recorder import RecorderAction
from dotfiles_api.infrastructure.actions.portal import PortalAction
from dotfiles_api.infrastructure.actions.drawer import DrawerAction
from dotfiles_api.infrastructure.actions.wallpaper import WallpaperAction

def main() -> None:
    parser = argparse.ArgumentParser(description="Modular Dotfiles API CLI Manager")
    parser.add_argument("--dry-run", action="store_true", help="Log commands instead of running them")
    parser.add_argument("--theme", default="shade-raid", help="The name of the theme to apply")
    parser.add_argument("command", choices=["install", "link", "configure", "reload", "apply-all", "toggle", "action", "setup"], help="Command to execute")
    parser.add_argument("action_name", nargs="?", help="Action name to run (required for action command)")
    parser.add_argument("action_args", nargs=argparse.REMAINDER, help="Arguments passed to the action")
    parser.add_argument("--github", action="store_true", help="Run GitHub authentication login during setup")
    
    args = parser.parse_args()

    home_dir = Path.home()
    dotfiles_dir = home_dir / "dotfiles"
    try:
        user = os.getlogin()
    except Exception:
        user = getpass.getuser()

    env = EnvironmentContext(home_dir=home_dir, dotfiles_dir=dotfiles_dir, user=user)
    
    executor = SystemCommandExecutor()
    exec_ctx = ExecutionContext(dry_run=args.dry_run, executor=executor)

    package_mapping = {
        # AUR packages
        "hyprlock": "yay",
        "hypridle": "yay",
        "hyprsunset": "yay",
        "hyprpicker": "yay",
        "hyprshot": "yay",
        "greetd": "yay",
        "greetd-regreet": "yay",
        "walker-bin": "yay",
        "elephant-all": "yay",
        "swayosd-git": "yay",
        "bluetui": "yay",
        "wlogout": "yay",
        "mise-bin": "yay",
        "bibata-cursor-theme": "yay",
        "papirus-folders": "yay",
        "vesktop-bin": "yay",
        "heroic-games-launcher-bin": "yay",
        "bitwarden": "yay",
        "spotify": "yay",
        "spicetify-cli": "yay",
        "zen-browser-bin": "yay",
        "ttf-iosevka-nerd": "yay",
        "otf-bebas-neue": "yay",
        
        # Pacman packages
        "hyprland": "pacman",
        "xdg-desktop-portal-hyprland": "pacman",
        "xdg-desktop-portal-gtk": "pacman",
        "waybar": "pacman",
        "sassc": "pacman",
        "jq": "pacman",
        "pipewire": "pacman",
        "pipewire-pulse": "pacman",
        "pipewire-alsa": "pacman",
        "wireplumber": "pacman",
        "networkmanager": "pacman",
        "network-manager-applet": "pacman",
        "openvpn": "pacman",
        "network-manager-openvpn": "pacman",
        "bluez": "pacman",
        "bluez-utils": "pacman",
        "awww": "pacman",
        "swaync": "pacman",
        "rofi-wayland": "pacman",
        "ghostty": "pacman",
        "fish": "pacman",
        "starship": "pacman",
        "grim": "pacman",
        "slurp": "pacman",
        "wl-clipboard": "pacman",
        "libnotify": "pacman",
        "cliphist": "pacman",
        "pacman-contrib": "pacman",
        "wf-recorder": "pacman",
        "brightnessctl": "pacman",
        "playerctl": "pacman",
        "mpv": "pacman",
        "imv": "pacman",
        "pavucontrol": "pacman",
        "nwg-look": "pacman",
        "qt6ct": "pacman",
        "qt5ct": "pacman",
        "papirus-icon-theme": "pacman",
        "polkit-gnome": "pacman",
        "nautilus": "pacman",
        "tumbler": "pacman",
        "ffmpegthumbnailer": "pacman",
        "file-roller": "pacman",
        "stow": "pacman",
        "btop": "pacman",
        "bc": "pacman",
        "ufw": "pacman",
        "reflector": "pacman",
        "xdg-user-dirs": "pacman",
        "openssh": "pacman",
        "imagemagick": "pacman",
        "neovim": "pacman",
        "lazygit": "pacman",
        "github-cli": "pacman",
        "bat": "pacman",
        "eza": "pacman",
        "fzf": "pacman",
        "zoxide": "pacman",
        "ripgrep": "pacman",
        "fd": "pacman",
        "git-delta": "pacman",
        "python-pip": "pacman",
        "ttf-jetbrains-mono-nerd": "pacman",
        "ttf-liberation": "pacman",
        "otf-monaspace": "pacman",
        "unzip": "pacman",
        "zip": "pacman",
        "mesa": "pacman",
        "lib32-mesa": "pacman",
        "vulkan-radeon": "pacman",
        "lib32-vulkan-radeon": "pacman",
        "libva-mesa-driver": "pacman",
        "libva-utils": "pacman",
        "gamescope": "pacman",
        "steam": "pacman",
        "gnome-keyring": "pacman",
        "seahorse": "pacman"
    }
    package_registry = PackageRegistry(mapping=package_mapping)

    artifact_paths = {
        "hyprland-colors": env.home_dir / ".config" / "hypr" / "colors.lua",
        "hyprland-style": env.home_dir / ".config" / "hypr" / "style.lua",
        "hyprland-colors-conf": env.home_dir / ".config" / "hypr" / "colors.conf",
        "hyprland-style-conf": env.home_dir / ".config" / "hypr" / "style.conf",
        "waybar-colors": env.home_dir / ".config" / "waybar" / "colors.scss",
        "waybar-variables": env.home_dir / ".config" / "waybar" / "variables.scss",
        "ghostty-colors": env.home_dir / ".config" / "ghostty" / "colors.conf",
        "swaync-style": env.home_dir / ".config" / "swaync" / "style.css",
        "swayosd-colors": env.home_dir / ".config" / "swayosd" / "_colors.scss",
        "btop-theme": env.home_dir / ".config" / "btop" / "themes" / "shade-raid.theme",
        "btop-config": env.home_dir / ".config" / "btop" / "btop.conf",
        "walker-colors": env.home_dir / ".config" / "walker" / "themes" / "{theme_name}" / "_colors.scss",
        "walker-config": env.home_dir / ".config" / "walker" / "config.toml",
        "wlogout-colors": env.home_dir / ".config" / "wlogout" / "_colors.scss",
        "vesktop-theme": env.home_dir / ".config" / "vesktop" / "themes" / "{theme_name}.theme.css",
        "hyprlock-config": env.home_dir / ".config" / "hypr" / "hyprlock.conf",
        "regreet-style": env.home_dir / ".config" / "greetd" / "regreet.css",
        "greetd-config": Path("/etc/greetd/regreet.toml"),
        "gtk3-settings": env.home_dir / ".config" / "gtk-3.0" / "settings.ini",
        "gtk4-settings": env.home_dir / ".config" / "gtk-4.0" / "settings.ini",
        "gtk3-css": env.home_dir / ".config" / "gtk-3.0" / "gtk.css",
        "gtk4-css": env.home_dir / ".config" / "gtk-4.0" / "gtk.css",
        "plymouth-theme": env.dotfiles_dir / "plymouth-shade-raid" / "shade-raid.script"
    }
    artifact_store = ArtifactStore(mappings=artifact_paths)

    file_writer = SystemFileWriter()
    theme_store = FileThemeStore(env=env)
    linker = StowLinker(exec_ctx=exec_ctx)

    pacman_src = PacmanSource(exec_ctx=exec_ctx)
    yay_src = YaySource(exec_ctx=exec_ctx)
    sources = {"pacman": pacman_src, "yay": yay_src}

    waybar_reload = WaybarReloadable(exec_ctx=exec_ctx)
    swaync_reload = SwayNCReloadable(exec_ctx=exec_ctx)
    portal_reload = XDGPortalReloadable(exec_ctx=exec_ctx)
    gsettings_reload = GsettingsReloadable(exec_ctx=exec_ctx, theme_store=theme_store)
    ghostty_reload = GhosttyReloadable(exec_ctx=exec_ctx)
    walker_reload = WalkerReloadable(exec_ctx=exec_ctx)
    wlogout_reload = WlogoutReloadable(exec_ctx=exec_ctx)
    btop_reload = BtopReloadable(exec_ctx=exec_ctx)
    hyprland_reload = HyprlandReloadable(exec_ctx=exec_ctx)

    reloadables = [
        waybar_reload,
        swaync_reload,
        portal_reload,
        gsettings_reload,
        ghostty_reload,
        walker_reload,
        wlogout_reload,
        btop_reload,
        hyprland_reload
    ]

    install_svc = InstallService(
        env=env,
        exec_ctx=exec_ctx,
        registry=package_registry,
        sources=sources
    )

    theme_loader = ThemeLoader(env=env)
    event_bus = EventBus()
    theme_svc = ThemeService(loader=theme_loader, store=theme_store, event_bus=event_bus)

    reload_svc = ReloadService(reloadables=reloadables)
    event_bus.subscribe(ConfigGeneratedEvent, reload_svc.handle_config_generated)

    tx = ConfigTransaction(env=env, store=artifact_store, writer=file_writer, dry_run=args.dry_run)
    
    generators = [
        HyprlandGenerator(name="hyprland", transaction=tx, event_bus=event_bus),
        WaybarGenerator(name="waybar", transaction=tx, event_bus=event_bus),
        GhosttyGenerator(name="ghostty", transaction=tx, event_bus=event_bus),
        SwayncGenerator(name="swaync", transaction=tx, event_bus=event_bus),
        SwayosdGenerator(name="swayosd", transaction=tx, event_bus=event_bus),
        BtopGenerator(name="btop", transaction=tx, event_bus=event_bus),
        WalkerGenerator(name="walker", transaction=tx, event_bus=event_bus),
        WlogoutGenerator(name="wlogout", transaction=tx, event_bus=event_bus),
        VesktopGenerator(name="vesktop", transaction=tx, event_bus=event_bus),
        HyprlockGenerator(name="hyprlock", transaction=tx, event_bus=event_bus),
        ReGreetGenerator(name="regreet", transaction=tx, event_bus=event_bus),
        GreetdGenerator(name="greetd", transaction=tx, event_bus=event_bus),
        GtkGenerator(name="gtk", transaction=tx, event_bus=event_bus),
        PlymouthGenerator(name="plymouth", transaction=tx, event_bus=event_bus)
    ]

    for gen in generators:
        event_bus.subscribe(ThemeChangedEvent, gen.handle_theme_changed)

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

    services_setup_svc = ServicesSetupService(exec_ctx, env)
    user_setup_svc = UserSetupService(exec_ctx, env)
    extras_setup_svc = ExtrasSetupService(exec_ctx, env)
    setup_svc = SetupService(
        env=env,
        exec_ctx=exec_ctx,
        install_service=install_svc,
        linker=linker,
        theme_service=theme_svc,
        services_service=services_setup_svc,
        user_service=user_setup_svc,
        extras_service=extras_setup_svc
    )

    facade = DotfilesFacade(
        env=env,
        exec_ctx=exec_ctx,
        install_service=install_svc,
        theme_service=theme_svc,
        reload_service=reload_svc,
        linker=linker,
        setup_service=setup_svc
    )

    action_svc = ActionService()
    action_svc.register("screenshot", ScreenshotAction(exec_ctx))
    action_svc.register("record", RecorderAction(exec_ctx))
    action_svc.register("portal", PortalAction(exec_ctx))
    action_svc.register("drawer", DrawerAction(exec_ctx, env))
    action_svc.register("wallpaper", WallpaperAction(exec_ctx, env))

    action_svc.register("lock", CommandAction(exec_ctx, [["loginctl", "lock-session"]]))
    action_svc.register("file-explorer", CommandAction(exec_ctx, [["nautilus"]]))
    action_svc.register("volume-up", CommandAction(exec_ctx, [["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%+"], ["swayosd-client", "--output-volume", "raise"]]))
    action_svc.register("volume-down", CommandAction(exec_ctx, [["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "5%-"], ["swayosd-client", "--output-volume", "lower"]]))
    action_svc.register("volume-mute", CommandAction(exec_ctx, [["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], ["swayosd-client", "--output-volume", "mute-toggle"]]))
    action_svc.register("brightness-up", CommandAction(exec_ctx, [["brightnessctl", "set", "5%+"], ["swayosd-client", "--brightness", "raise"]]))
    action_svc.register("brightness-down", CommandAction(exec_ctx, [["brightnessctl", "set", "5%-"], ["swayosd-client", "--brightness", "lower"]]))
    action_svc.register("media-play", CommandAction(exec_ctx, [["playerctl", "play-pause"]]))
    action_svc.register("media-next", CommandAction(exec_ctx, [["playerctl", "next"]]))
    action_svc.register("media-prev", CommandAction(exec_ctx, [["playerctl", "previous"]]))

    if args.command in ["toggle", "configure", "apply-all", "install"]:
        import fcntl
        lock_file_path = "/tmp/dotfiles.lock"
        try:
            global _lock_file
            _lock_file = open(lock_file_path, "w")
            fcntl.flock(_lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            import atexit
            def cleanup_lock():
                try:
                    global _lock_file
                    _lock_file.close()
                    import os
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
                except Exception:
                    pass
            atexit.register(cleanup_lock)
        except BlockingIOError:
            print("Another dotfiles configuration process is already running. Exiting.")
            import sys
            sys.exit(0)

    if args.command == "install":
        facade.apply_profile(desktop_profile)
    elif args.command == "link":
        facade.link()
    elif args.command == "configure":
        facade.apply_theme(args.theme)
    elif args.command == "reload":
        facade.reload()
    elif args.command == "apply-all":
        facade.apply_profile(desktop_profile)
        facade.link()
        facade.apply_theme(args.theme)
        facade.reload()
    elif args.command == "toggle":
        active = theme_store.get_active_theme()
        if active.endswith("-dark"):
            next_theme = active[:-5]
        else:
            next_theme = active + "-dark"
        print(f"Toggling theme from {active} to {next_theme}")
        facade.apply_theme(next_theme)
    elif args.command == "setup":
        facade.setup(setup_github=args.github)
    elif args.command == "action":
        if not args.action_name:
            parser.error("action_name is required for the 'action' command")
        action_svc.run_action(args.action_name, args.action_args or [])

if __name__ == "__main__":
    main()
