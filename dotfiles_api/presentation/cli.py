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

def main() -> None:
    parser = argparse.ArgumentParser(description="Modular Dotfiles API CLI Manager")
    parser.add_argument("--dry-run", action="store_true", help="Log commands instead of running them")
    parser.add_argument("--theme", default="shade-raid", help="The name of the theme to apply")
    parser.add_argument("command", choices=["install", "link", "configure", "reload", "apply-all", "toggle"], help="Command to execute")
    
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
        "ghostty": "pacman",
        "waybar": "pacman",
        "swaync": "pacman",
        "hyprland": "pacman",
        "walker": "pacman",
        "hyprsunset": "pacman",
        "hypridle": "pacman",
        "playerctl": "pacman",
        "brightnessctl": "pacman",
        "zoxide": "pacman",
        "starship": "pacman",
        "stow": "pacman",
        "xdg-user-dirs": "pacman",
        "bat": "pacman",
        "eza": "pacman",
        "libnotify": "pacman",
        "zen-browser-bin": "yay",
        "vesktop-bin": "yay",
        "awww": "yay"
    }
    package_registry = PackageRegistry(mapping=package_mapping)

    artifact_paths = {
        "hyprland-colors": env.home_dir / ".config" / "hypr" / "colors.lua",
        "hyprland-style": env.home_dir / ".config" / "hypr" / "style.lua",
        "hyprland-colors-conf": env.home_dir / ".config" / "hypr" / "colors.conf",
        "hyprland-style-conf": env.home_dir / ".config" / "hypr" / "style.conf",
        "waybar-colors": env.home_dir / ".config" / "waybar" / "colors.scss",
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
        Feature(name="launcher", packages=["walker"], capabilities=["launcher"]),
        Feature(name="statusbar", packages=["waybar"], capabilities=["status-bar"]),
        Feature(name="notifications", packages=["swaync", "libnotify"], capabilities=["notification-center"]),
        Feature(name="compositor", packages=["hyprland", "hyprsunset", "hypridle", "awww"], capabilities=["compositor"]),
        Feature(name="terminal", packages=["ghostty"], capabilities=["terminal"]),
        Feature(name="shell", packages=["zoxide", "starship", "bat", "eza", "stow"], capabilities=["shell"])
    ]
    desktop_profile = Profile(name="desktop", features=features)

    facade = DotfilesFacade(
        env=env,
        exec_ctx=exec_ctx,
        install_service=install_svc,
        theme_service=theme_svc,
        reload_service=reload_svc,
        linker=linker
    )

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
        facade.reload()

if __name__ == "__main__":
    main()
