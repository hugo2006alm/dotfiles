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
from dotfiles_api.infrastructure.reloadables.waybar import WaybarReloadable
from dotfiles_api.infrastructure.reloadables.swaync import SwayNCReloadable
from dotfiles_api.infrastructure.reloadables.portal import XDGPortalReloadable
from dotfiles_api.infrastructure.generators.hypr import HyprlandGenerator
from dotfiles_api.infrastructure.generators.waybar import WaybarGenerator
from dotfiles_api.infrastructure.registry.generators import GeneratorRegistry
from dotfiles_api.infrastructure.registry.capabilities import CapabilityRegistry

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
    parser.add_argument("command", choices=["install", "link", "configure", "reload", "apply-all"], help="Command to execute")
    
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
        "waybar-colors": env.home_dir / ".config" / "waybar" / "colors.scss"
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
    reloadables = [waybar_reload, swaync_reload, portal_reload]

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

    tx = ConfigTransaction(env=env, store=artifact_store, writer=file_writer)
    hypr_gen = HyprlandGenerator(name="hyprland", transaction=tx, event_bus=event_bus)
    waybar_gen = WaybarGenerator(name="waybar", transaction=tx, event_bus=event_bus)

    event_bus.subscribe(ThemeChangedEvent, hypr_gen.handle_theme_changed)
    event_bus.subscribe(ThemeChangedEvent, waybar_gen.handle_theme_changed)

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

if __name__ == "__main__":
    main()
