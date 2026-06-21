import unittest
import tempfile
import shutil
from pathlib import Path
from dotfiles_api.domain.tokens import DesignTokens, ColorTokens, MetricTokens, TypographyTokens
from dotfiles_api.domain.events import EventBus, ThemeChangedEvent, ConfigGeneratedEvent
from dotfiles_api.domain.models import Feature, Profile
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.application.loader import ThemeLoader
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.services.theme import ThemeService
from dotfiles_api.application.services.reload import ReloadService
from dotfiles_api.infrastructure.package_sources import PacmanSource, YaySource
from dotfiles_api.infrastructure.linker import StowLinker
from dotfiles_api.infrastructure.reloadables import WaybarReloadable, SwayNCReloadable, XDGPortalReloadable
from dotfiles_api.infrastructure.capabilities.walker import WalkerLauncher
from dotfiles_api.infrastructure.capabilities.waybar import WaybarStatusBar
from dotfiles_api.infrastructure.capabilities.swaync import SwayNCNotificationCenter
from dotfiles_api.infrastructure.capabilities.hyprland import HyprlandCompositor

class MockCommandExecutor:
    def __init__(self):
        self.commands = []

    def execute(self, args: list[str], cwd: Path | None = None) -> CommandResult:
        self.commands.append(" ".join(args))
        return CommandResult(stdout="", stderr="", returncode=0)

class MockThemeStore:
    def __init__(self):
        self.theme = "shade-raid"

    def get_active_theme(self) -> str:
        return self.theme

    def set_active_theme(self, theme_name: str) -> None:
        self.theme = theme_name

class MockPackageSource:
    def __init__(self, available=True):
        self.installed = []
        self._available = available

    def is_available(self) -> bool:
        return self._available

    def install(self, packages: list[str]) -> None:
        self.installed.extend(packages)

class MockReloadable:
    def __init__(self):
        self.reloaded = False

    def reload(self) -> None:
        self.reloaded = True

class TestPackageRegistry(unittest.TestCase):
    def test_resolve_source(self):
        # Arrange
        mapping = {"ghostty": "pacman", "walker": "yay"}
        reg = PackageRegistry(mapping=mapping)

        # Assert
        self.assertEqual(reg.resolve_source("ghostty"), "pacman")
        self.assertEqual(reg.resolve_source("walker"), "yay")
        self.assertEqual(reg.resolve_source("unknown"), "pacman")  # default

class TestThemeLoader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.env = EnvironmentContext(
            home_dir=Path(self.temp_dir),
            dotfiles_dir=Path(self.temp_dir) / "dotfiles",
            user="user"
        )
        # Create a mock colors.toml
        themes_dir = self.env.home_dir / ".config" / "themes" / "shade-raid"
        themes_dir.mkdir(parents=True, exist_ok=True)
        toml_content = """
[colors]
background = "#F4EFE4"
foreground = "#0D0D0D"
accent = "#D94F2B"
inactive = "#C8C2B4"

[metrics]
border_size = 2
gaps_inner = 10
gaps_outer = 15
corner_radius = 8

[typography]
sans = "Outfit"
font_size = 11
"""
        (themes_dir / "colors.toml").write_text(toml_content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_theme_loading_pure(self):
        # Arrange
        loader = ThemeLoader(env=self.env)

        # Act
        tokens = loader.load("shade-raid")

        # Assert
        self.assertEqual(tokens.colors.colors["background"], "#F4EFE4")
        self.assertEqual(tokens.colors.colors["accent"], "#D94F2B")
        self.assertEqual(tokens.metrics.metrics["border_size"], 2)
        self.assertEqual(tokens.metrics.metrics["gaps_inner"], 10)
        self.assertEqual(tokens.typography.typography["sans"], "Outfit")
        self.assertEqual(tokens.typography.typography["font_size"], 11)

class TestInstallService(unittest.TestCase):
    def test_profile_package_routing(self):
        # Arrange
        registry = PackageRegistry({"ghostty": "pacman", "walker": "yay"})
        pacman_src = MockPackageSource()
        yay_src = MockPackageSource()
        sources = {"pacman": pacman_src, "yay": yay_src}
        
        install_svc = InstallService(
            env=None,
            exec_ctx=None,
            registry=registry,
            sources=sources
        )

        f1 = Feature(name="launcher", packages=["walker"], capabilities=[])
        f2 = Feature(name="terminal", packages=["ghostty"], capabilities=[])
        profile = Profile(name="dev", features=[f1, f2])

        # Act
        install_svc.install_profile(profile)

        # Assert
        self.assertEqual(pacman_src.installed, ["ghostty"])
        self.assertEqual(yay_src.installed, ["walker"])

class TestThemeService(unittest.TestCase):
    def test_theme_application(self):
        # Arrange
        bus = EventBus()
        events = []
        bus.subscribe(ThemeChangedEvent, lambda e: events.append(e))

        # Mock Loader
        class DummyLoader:
            def load(self, name):
                return DesignTokens(
                    colors=ColorTokens(colors={"bg": "#111"}),
                    metrics=MetricTokens(metrics={}),
                    typography=TypographyTokens(typography={})
                )
        
        store = MockThemeStore()
        theme_svc = ThemeService(loader=DummyLoader(), store=store, event_bus=bus)

        # Act
        theme_svc.apply_theme("catppuccin")

        # Assert
        self.assertEqual(store.get_active_theme(), "catppuccin")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].tokens.colors.colors["bg"], "#111")

class TestReloadService(unittest.TestCase):
    def test_reload_all(self):
        # Arrange
        r1 = MockReloadable()
        r2 = MockReloadable()
        reload_svc = ReloadService(reloadables=[r1, r2])

        # Act
        reload_svc.reload_all()

        # Assert
        self.assertTrue(r1.reloaded)
        self.assertTrue(r2.reloaded)

    def test_reload_on_event(self):
        # Arrange
        r = MockReloadable()
        bus = EventBus()
        reload_svc = ReloadService(reloadables=[r])
        bus.subscribe(ConfigGeneratedEvent, reload_svc.handle_config_generated)

        # Act
        bus.publish(ConfigGeneratedEvent(generator_name="waybar"))

        # Assert
        self.assertTrue(r.reloaded)

class TestInfrastructureImplementations(unittest.TestCase):
    def test_pacman_source(self):
        # Arrange
        executor = MockCommandExecutor()
        exec_ctx = ExecutionContext(dry_run=False, executor=executor)
        source = PacmanSource(exec_ctx=exec_ctx)

        # Act
        source.install(["git", "curl"])

        # Assert
        self.assertEqual(len(executor.commands), 1)
        self.assertIn("sudo pacman -S --needed --noconfirm git curl", executor.commands[0])

    def test_yay_source(self):
        # Arrange
        executor = MockCommandExecutor()
        exec_ctx = ExecutionContext(dry_run=False, executor=executor)
        source = YaySource(exec_ctx=exec_ctx)

        # Act
        source.install(["walker"])

        # Assert
        self.assertEqual(len(executor.commands), 1)
        self.assertIn("yay -S --needed --noconfirm walker", executor.commands[0])

    def test_stow_linker(self):
        # Arrange
        executor = MockCommandExecutor()
        exec_ctx = ExecutionContext(dry_run=False, executor=executor)
        linker = StowLinker(exec_ctx=exec_ctx)

        # Act
        linker.link(Path("/src"), Path("/dest"))

        # Assert
        self.assertEqual(len(executor.commands), 1)
        self.assertEqual(executor.commands[0], "stow -d /src -t /dest .")

    def test_waybar_reloadable(self):
        # Arrange
        executor = MockCommandExecutor()
        exec_ctx = ExecutionContext(dry_run=False, executor=executor)
        reloadable = WaybarReloadable(exec_ctx=exec_ctx)

        # Act
        reloadable.reload()

        # Assert
        self.assertEqual(len(executor.commands), 1)
        self.assertIn("pkill waybar", executor.commands[0])

    def test_swaync_reloadable(self):
        # Arrange
        executor = MockCommandExecutor()
        exec_ctx = ExecutionContext(dry_run=False, executor=executor)
        reloadable = SwayNCReloadable(exec_ctx=exec_ctx)

        # Act
        reloadable.reload()

        # Assert
        self.assertEqual(len(executor.commands), 1)
        self.assertIn("swaync-client -R", executor.commands[0])

    def test_walker_launcher_capability(self):
        # Arrange
        executor = MockCommandExecutor()
        exec_ctx = ExecutionContext(dry_run=False, executor=executor)
        launcher = WalkerLauncher(exec_ctx=exec_ctx)

        # Act
        launcher.launch()

        # Assert
        self.assertEqual(len(executor.commands), 1)
        self.assertEqual(executor.commands[0], "walker")
