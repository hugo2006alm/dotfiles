import argparse
import sys
import os
import getpass
from contextlib import nullcontext
from dotfiles_api.presentation.argument_parser import CommandParser
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
from dotfiles_api.infrastructure.reloadables.vesktop import VesktopReloadable
from dotfiles_api.infrastructure.reloadables.regreet import ReGreetReloadable

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

from dotfiles_api.application.profiles.resolver import DesktopProfileResolver
from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.theme_coordinator import ThemeCoordinator
from dotfiles_api.infrastructure.runtime_lock import RuntimeLock
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.services.theme import ThemeService
from dotfiles_api.application.services.reload import ReloadService
from dotfiles_api.application.facade import DotfilesFacade
from dotfiles_api.domain.events import EventBus, ThemeChangedEvent, ConfigGeneratedEvent

# Setup services
from dotfiles_api.application.services.services import ServicesSetupService
from dotfiles_api.application.services.user import UserSetupService
from dotfiles_api.application.services.extras import ExtrasSetupService
from dotfiles_api.application.services.setup import SetupService
from dotfiles_api.application.services.login import LoginSetupService

# Actions
from dotfiles_api.application.services.action import ActionService
from dotfiles_api.infrastructure.actions.command import CommandAction
from dotfiles_api.infrastructure.actions.screenshot import ScreenshotAction
from dotfiles_api.infrastructure.actions.recorder import RecorderAction
from dotfiles_api.infrastructure.actions.portal import PortalAction
from dotfiles_api.infrastructure.actions.drawer import DrawerAction
from dotfiles_api.infrastructure.actions.wallpaper import WallpaperAction
from dotfiles_api.infrastructure.actions.preview import PreviewAction


def build_parser() -> argparse.ArgumentParser:
    parser = CommandParser(description="Modular Dotfiles API CLI Manager")
    parser.set_defaults(github=False)
    parser.add_argument("--dry-run", action="store_true", help="Log commands instead of running them")
    parser.add_argument("--theme", default="shade-raid", help="The name of the theme to apply")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--github", action="store_true", help="Run GitHub authentication login during setup")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "link", "configure", "reload", "apply-all", "toggle", "action", "setup", "setup-login", "rollback"):
        command = commands.add_parser(name)
        # Suppressed defaults preserve options given before the subcommand.
        command.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS)
        command.add_argument("--theme", default=argparse.SUPPRESS)
        command.add_argument("--verbose", "-v", action="store_true", default=argparse.SUPPRESS)
        if name == "setup":
            command.add_argument("--github", action="store_true", default=argparse.SUPPRESS)
            command.add_argument("--ssh-server", action="store_true", help="Enable incoming SSH and open its firewall rule")
        if name == "action":
            command.add_argument("action_name")
            command.add_argument("action_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    home_dir = Path.home()
    dotfiles_dir = Path(os.environ.get("DOTFILES_DIR", Path(__file__).resolve().parents[2]))
    try:
        user = os.getlogin()
    except Exception:
        user = getpass.getuser()

    env = EnvironmentContext(home_dir=home_dir, dotfiles_dir=dotfiles_dir, user=user,
                             state_home=Path(os.environ["XDG_STATE_HOME"]) if os.environ.get("XDG_STATE_HOME") else None,
                             runtime_home=Path(os.environ["XDG_RUNTIME_DIR"]) if os.environ.get("XDG_RUNTIME_DIR") else None)

    executor = SystemCommandExecutor()
    exec_ctx = ExecutionContext(dry_run=args.dry_run, executor=executor,
                                verbose=getattr(args, "verbose", False),
                                log_path=env.state_dir / "commands.jsonl")

    package_registry = PackageRegistry()

    artifact_paths = {
        "active-theme": env.state_dir / "active-theme",
        "theme-preview": env.runtime_dir / "preview-theme",
        "hyprland-colors": env.home_dir / ".config" / "hypr" / "colors.lua",
        "hyprland-style": env.home_dir / ".config" / "hypr" / "style.lua",
        "hyprland-colors-conf": env.home_dir / ".config" / "hypr" / "colors.conf",
        "hyprland-style-conf": env.home_dir / ".config" / "hypr" / "style.conf",
        "waybar-colors": env.home_dir / ".config" / "waybar" / "colors.scss",
        "waybar-variables": env.home_dir / ".config" / "waybar" / "variables.scss",
        "ghostty-colors": env.home_dir / ".config" / "ghostty" / "colors.conf",
        "swaync-config": env.home_dir / ".config" / "swaync" / "config.json",
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
        "greetd-config": env.home_dir / ".config" / "greetd" / "regreet.toml",
        "gtk3-settings": env.home_dir / ".config" / "gtk-3.0" / "settings.ini",
        "gtk4-settings": env.home_dir / ".config" / "gtk-4.0" / "settings.ini",
        "gtk3-css": env.home_dir / ".config" / "gtk-3.0" / "gtk.css",
        "gtk4-css": env.home_dir / ".config" / "gtk-4.0" / "gtk.css",
        "plymouth-theme": env.state_dir / "generated" / "plymouth" / "shade-raid.script",
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
    gsettings_reload = GsettingsReloadable(exec_ctx=exec_ctx, theme_store=theme_store, loader=ThemeLoader(env))
    ghostty_reload = GhosttyReloadable(exec_ctx=exec_ctx)
    walker_reload = WalkerReloadable(exec_ctx=exec_ctx)
    wlogout_reload = WlogoutReloadable(exec_ctx=exec_ctx)
    btop_reload = BtopReloadable(exec_ctx=exec_ctx)
    hyprland_reload = HyprlandReloadable(exec_ctx=exec_ctx)
    vesktop_reload = VesktopReloadable(exec_ctx=exec_ctx, theme_store=theme_store)
    regreet_reload = ReGreetReloadable(exec_ctx=exec_ctx, env=env)

    reloadables = [
        waybar_reload,
        swaync_reload,
        portal_reload,
        gsettings_reload,
        ghostty_reload,
        walker_reload,
        wlogout_reload,
        btop_reload,
        hyprland_reload,
        vesktop_reload,
        regreet_reload,
    ]

    install_svc = InstallService(
        env=env,
        exec_ctx=exec_ctx,
        registry=package_registry,
        sources=sources,
    )

    theme_loader = ThemeLoader(env=env)
    event_bus = EventBus()

    reload_svc = ReloadService(reloadables=reloadables, verbose=getattr(args, "verbose", False), dry_run=args.dry_run, runtime_dir=env.runtime_dir)

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
        PlymouthGenerator(name="plymouth", transaction=tx, event_bus=event_bus),
    ]

    planner = ThemePlanner(env, artifact_store, generators)
    coordinator = ThemeCoordinator(env, planner, tx)
    theme_svc = ThemeService(theme_loader, theme_store, event_bus, planner=planner,
                             dry_run=args.dry_run, coordinator=coordinator,
                             on_applied=reload_svc.reload_changed)

    profile_resolver = DesktopProfileResolver()
    desktop_profile = profile_resolver.resolve()

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
        extras_service=extras_setup_svc,
        profile_resolver=profile_resolver,
    )

    facade = DotfilesFacade(
        env=env,
        exec_ctx=exec_ctx,
        install_service=install_svc,
        theme_service=theme_svc,
        reload_service=reload_svc,
        linker=linker,
        setup_service=setup_svc,
    )

    action_svc = ActionService()
    action_svc.register("screenshot", ScreenshotAction(exec_ctx))
    action_svc.register("record", RecorderAction(exec_ctx, env))
    action_svc.register("portal", PortalAction(exec_ctx))
    action_svc.register("drawer", DrawerAction(exec_ctx, env))
    action_svc.register("wallpaper", WallpaperAction(exec_ctx, env))
    action_svc.register("preview", PreviewAction(exec_ctx, env))

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

    def apply_theme(name):
        plan = facade.apply_theme(name)
        if not args.dry_run and (plan is None or plan.changed_generators):
            action_svc.run_action("wallpaper", [])

    def dispatch():
        if args.command == "install":
            facade.apply_profile(desktop_profile)
        elif args.command == "link":
            facade.link()
        elif args.command == "configure":
            apply_theme(args.theme)
        elif args.command == "reload":
            facade.reload()
        elif args.command == "apply-all":
            facade.apply_profile(desktop_profile)
            facade.link()
            apply_theme(args.theme)
        elif args.command == "toggle":
            active = theme_store.get_active_theme()
            next_theme = active[:-5] if active.endswith("-dark") else active + "-dark"
            print(f"Toggling theme from {active} to {next_theme}")
            apply_theme(next_theme)
        elif args.command == "rollback":
            facade.rollback()
            if not args.dry_run:
                action_svc.run_action("wallpaper", [])
        elif args.command == "setup":
            facade.setup(setup_github=args.github, enable_ssh_server=getattr(args, "ssh_server", False))
        elif args.command == "setup-login":
            LoginSetupService(exec_ctx, env).apply()
        elif args.command == "action":
            action_svc.run_action(args.action_name, args.action_args or [])

    mutating = args.command in {"configure", "toggle", "apply-all", "install", "setup", "link", "rollback"}
    if not args.dry_run and mutating:
        env.validate_output_path(env.lock_dir / "configure.lock")
    lock = RuntimeLock(env.lock_dir / "configure.lock") if mutating and not args.dry_run else nullcontext()
    with lock:
        dispatch()


if __name__ == "__main__":
    main()
