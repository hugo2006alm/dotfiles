import argparse
import sys
import os
import getpass
from contextlib import nullcontext
from dotfiles_api.presentation.argument_parser import CommandParser
from pathlib import Path

from dotfiles_api.presentation.argument_parser import CommandParser
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.infrastructure.executor import SystemCommandExecutor
from dotfiles_api.infrastructure.file_writer import SystemFileWriter
from dotfiles_api.infrastructure.file_store import FileThemeStore
from dotfiles_api.infrastructure.linker import StowLinker
from dotfiles_api.infrastructure.package_sources.pacman import PacmanSource
from dotfiles_api.infrastructure.package_sources.yay import YaySource



from dotfiles_api.application.profiles.resolver import DesktopProfileResolver
from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.application.application_registry import ApplicationRegistry
from dotfiles_api.infrastructure.application_catalog import APPLICATIONS
from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.application.store import ArtifactStore
from dotfiles_api.application.transaction import ConfigTransaction
from dotfiles_api.application.planner import ThemePlanner
from dotfiles_api.application.theme_coordinator import ThemeCoordinator
from dotfiles_api.infrastructure.theme_styler import ThemeStyler
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
from dotfiles_api.infrastructure.actions.session import SessionAction
from dotfiles_api.infrastructure.actions.media import MediaAction
from dotfiles_api.infrastructure.actions.control import ControlAction
from dotfiles_api.infrastructure.actions.browser import BrowserAction
from dotfiles_api.infrastructure.actions.launch import LaunchAction
from dotfiles_api.infrastructure.actions.clipboard import ClipboardAction
from dotfiles_api.application.services.wayland_session import WaylandSessionService
from dotfiles_api.infrastructure.actions.drawer import DrawerAction
from dotfiles_api.infrastructure.actions.wallpaper import WallpaperAction
from dotfiles_api.infrastructure.actions.preview import PreviewAction


def build_parser() -> argparse.ArgumentParser:
    parser = CommandParser(description="Modular Dotfiles API CLI Manager", allow_abbrev=False)
    parser.set_defaults(github=False)
    parser.add_argument("--dry-run", action="store_true", help="Log commands instead of running them")
    parser.add_argument("--theme", default=None, help="The name of the theme to apply")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--github", action="store_true", help="Run GitHub authentication login during setup")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "link", "configure", "reload", "apply-all", "toggle", "action", "setup", "setup-login", "repair-login-permissions", "rollback"):
        command = commands.add_parser(name, allow_abbrev=False)
        # Suppressed defaults preserve options given before the subcommand.
        command.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS)
        if name in {"configure", "apply-all", "setup"}:
            command.add_argument("--theme", default=argparse.SUPPRESS)
        command.add_argument("--verbose", "-v", action="store_true", default=argparse.SUPPRESS)
        if name in {"install", "apply-all", "setup"}:
            command.add_argument("--profile", dest="profiles", action="append", help="Composable software profile (repeatable)")
            command.add_argument("--package", dest="packages", action="append", help="Additional package (repeatable)")
        if name == "setup":
            command.add_argument("--interactive", action="store_true", help="Select optional packages interactively")
            command.add_argument("--change-shell", action="store_true", help="Explicitly set Fish as login shell")
            command.add_argument("--github", action="store_true", default=argparse.SUPPRESS)
            command.add_argument("--ssh-server", action="store_true", help="Enable the SSH server; configure firewall access separately")
        if name == "action":
            command.add_argument("action_name")
            command.add_argument("action_args", nargs=argparse.REMAINDER)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command in {"configure", "apply-all"} and args.theme is None:
        args.theme = "shade-raid"
    if args.command == "setup" and os.geteuid() == 0:
        raise RuntimeError("Run setup as a normal user, not root")

    for variable in ("DOTFILES_DIR", "XDG_STATE_HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_RUNTIME_DIR"):
        value = os.environ.get(variable)
        if value and not Path(value).is_absolute():
            raise ValueError(f"{variable} must be an absolute path")
        if value and Path(value).exists() and not Path(value).is_dir():
            raise ValueError(f"{variable} must name a directory")
    explicit_root = os.environ.get("DOTFILES_DIR")
    if explicit_root and not (Path(explicit_root) / "dotfiles_api" / "presentation" / "cli.py").is_file():
        raise ValueError("DOTFILES_DIR must point to a complete dotfiles checkout")

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
                                log_path=env.state_dir / "commands.jsonl",
                                output_guard=env.validate_output_path)

    package_registry = PackageRegistry()

    applications = ApplicationRegistry(APPLICATIONS)
    artifact_store = ArtifactStore(applications.artifact_paths(env, validate=args.command not in {"link", "setup"}))

    file_writer = SystemFileWriter()
    theme_store = FileThemeStore(env=env)
    linker = StowLinker(exec_ctx=exec_ctx)

    pacman_src = PacmanSource(exec_ctx=exec_ctx)
    yay_src = YaySource(exec_ctx=exec_ctx)
    sources = {"pacman": pacman_src, "yay": yay_src}

    theme_loader = ThemeLoader(env=env)
    reloadables = applications.reloadables(exec_ctx, env, theme_store, theme_loader)

    install_svc = InstallService(
        env=env,
        exec_ctx=exec_ctx,
        registry=package_registry,
        sources=sources,
    )

    theme_loader = ThemeLoader(env=env)
    event_bus = EventBus()

    reload_svc = ReloadService(reloadables=reloadables, verbose=getattr(args, "verbose", False), dry_run=args.dry_run, runtime_dir=env.runtime_dir,
                               pending_path=env.state_dir / "pending-refresh", output_guard=env.validate_output_path)

    tx = ConfigTransaction(env=env, store=artifact_store, writer=file_writer, dry_run=args.dry_run)

    generators = applications.generators(tx, event_bus)
    planner = ThemePlanner(env, artifact_store, generators, registry=applications)
    coordinator = ThemeCoordinator(env, planner, tx, ThemeStyler(env, applications, artifact_store, exec_ctx))
    theme_svc = ThemeService(theme_loader, theme_store, event_bus, planner=planner,
                             dry_run=args.dry_run, coordinator=coordinator,
                             on_applied=reload_svc.reload_changed)

    profile_resolver = DesktopProfileResolver()
    profiles = getattr(args, "profiles", None)
    packages = getattr(args, "packages", None)
    isolated = args.command == "install" and packages and not profiles
    desktop_profile = profile_resolver.resolve_profiles([] if isolated else profiles, packages) if profiles or packages else profile_resolver.resolve()

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
        selected_profiles=profiles,
        selected_packages=packages,
        interactive=getattr(args, "interactive", False),
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
    session = WaylandSessionService(exec_ctx, applications)
    action_svc.register("session", SessionAction(session))
    action_svc.register("screenshot", ScreenshotAction(exec_ctx))
    action_svc.register("record", RecorderAction(exec_ctx, env))
    action_svc.register("portal", PortalAction(exec_ctx, session))
    action_svc.register("drawer", DrawerAction(exec_ctx, env))
    action_svc.register("wallpaper", WallpaperAction(exec_ctx, env))
    action_svc.register("preview", PreviewAction(exec_ctx, env))
    action_svc.register("browser", BrowserAction(exec_ctx))
    action_svc.register("chatgpt", BrowserAction(exec_ctx, chatgpt=True))
    action_svc.register("launch", LaunchAction(exec_ctx, APPLICATIONS))
    action_svc.register("clipboard", ClipboardAction(exec_ctx, env))
    action_svc.register("clipboard-edit", ClipboardAction(exec_ctx, env, edit=True))

    action_svc.register("lock", CommandAction(exec_ctx, [["loginctl", "lock-session"]]))
    action_svc.register("file-explorer", CommandAction(exec_ctx, [["nautilus"]]))
    for kind, directions in (("volume", ("up", "down", "mute")), ("brightness", ("up", "down"))):
        for direction in directions:
            action_svc.register(f"{kind}-{direction}", ControlAction(exec_ctx, kind, direction))
    for name, command in (("play", "play-pause"), ("pause", "pause"), ("next", "next"), ("prev", "previous"), ("stop", "stop")):
        action_svc.register(f"media-{name}", MediaAction(exec_ctx, command))

    def apply_theme(name):
        try:
            plan = facade.apply_theme(name)
            if not args.dry_run and os.environ.get("WAYLAND_DISPLAY") and (plan is None or plan.changed_generators):
                action_svc.run_action("wallpaper", [])
                exec_ctx.optional(["notify-send", "Shade Raid", f"Theme applied: {name}"], step="theme:feedback")
        except Exception:
            if not args.dry_run and os.environ.get("WAYLAND_DISPLAY"):
                exec_ctx.optional(["notify-send", "--urgency=critical", "Shade Raid", "Theme action failed; run dotfiles doctor"], step="theme:feedback")
            raise

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
            if not args.dry_run and os.environ.get("WAYLAND_DISPLAY"):
                action_svc.run_action("wallpaper", [])
        elif args.command == "setup":
            options = {"setup_github": args.github, "enable_ssh_server": getattr(args, "ssh_server", False)}
            if getattr(args, "change_shell", False):
                options["change_shell"] = True
            if args.theme is not None:
                options["theme_name"] = args.theme
            facade.setup(**options)
        elif args.command in {"setup-login", "repair-login-permissions"}:
            LoginSetupService(exec_ctx, env).apply(permissions_only=args.command == "repair-login-permissions")
        elif args.command == "action":
            try:
                action_svc.run_action(args.action_name, args.action_args or [])
            except Exception:
                if not args.dry_run:
                    exec_ctx.optional(["notify-send", "--urgency=critical", "Shade Raid",
                                       f"Action failed: {args.action_name}"], step="action:feedback")
                raise

    mutating = args.command in {"configure", "toggle", "apply-all", "install", "setup", "link", "rollback"}
    if not args.dry_run and mutating:
        env.validate_output_path(env.lock_dir / "configure.lock")
    lock = RuntimeLock(env.lock_dir / "configure.lock") if mutating and not args.dry_run else nullcontext()
    with lock:
        dispatch()


if __name__ == "__main__":
    main()
