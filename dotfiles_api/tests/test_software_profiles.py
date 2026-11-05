import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.profiles.software import SoftwareProfileResolver
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.models.feature import Feature
from dotfiles_api.domain.models.profile import Profile


class TestSoftwareProfiles(unittest.TestCase):
    def test_profile_dependencies_are_composable_and_deduplicated(self):
        resolver = SoftwareProfileResolver()
        profile = resolver.resolve(["daily", "dev", "gaming"], graphics_packages=["vulkan-intel"])
        self.assertIn("core", profile.selected_profiles)
        self.assertIn("desktop", profile.selected_profiles)
        self.assertEqual(len(profile.get_packages()), len(set(profile.get_packages())))
        for package in ("zen-browser-bin", "vesktop-bin", "uv", "steam", "vulkan-intel"):
            self.assertIn(package, profile.get_packages())
        self.assertNotIn("ollama-rocm", profile.get_packages())
        self.assertNotIn("hyprland", resolver.resolve(["core"]).get_packages())
        self.assertNotIn("steam", resolver.resolve(["desktop"]).get_packages())
        with self.assertRaisesRegex(ValueError, "Unknown profile"):
            resolver.resolve(["typo"])

    def test_composed_profiles_include_application_install_dependencies(self):
        from dotfiles_api.domain.models.application_spec import ApplicationSpec
        from dotfiles_api.domain.models.profile_spec import ProfileSpec
        dependency = ApplicationSpec('dependency', packages=('dependency-pkg',), profiles=())
        consumer = ApplicationSpec('consumer', packages=('consumer-pkg',), profiles=('core',), dependencies=('dependency',))
        profile = SoftwareProfileResolver(applications=(consumer, dependency), profiles=(ProfileSpec('core'),)).resolve(['core'])
        self.assertEqual(profile.get_packages(), ['dependency-pkg', 'consumer-pkg'])

    def test_install_is_incremental_and_persists_successful_selections(self):
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / "repo", "tester")
            source = Mock()
            source.is_available.return_value = True
            source.contains.return_value = True
            service = InstallService(env, ExecutionContext(False, Mock()), PackageRegistry(), {"pacman": source},
                                     inventory=lambda: {"git"})
            profile = Profile("dev", [Feature("dev", ["git", "uv"], [])], selected_profiles=("core", "dev"))
            with contextlib.redirect_stdout(io.StringIO()) as output:
                service.install_profile(profile)
            self.assertIn("INSTALL PLAN", output.getvalue())
            source.install.assert_called_once_with(["uv"])
            state = json.loads((env.state_dir / "installation.json").read_text())
            self.assertEqual(state["profiles"], ["core", "dev"])
            self.assertEqual(state["packages"], ["git", "uv"])

    def test_preflight_failure_does_not_install_or_save_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / "repo", "tester")
            source = Mock()
            source.is_available.return_value = True
            source.contains.return_value = False
            service = InstallService(env, ExecutionContext(False, Mock()), PackageRegistry(), {"pacman": source},
                                     inventory=lambda: set())
            with self.assertRaisesRegex(RuntimeError, "unavailable.*missing|missing.*unavailable"), \
                    contextlib.redirect_stdout(io.StringIO()):
                service.install_profile(Profile("test", [Feature("test", ["missing"], [])]))
            source.install.assert_not_called()
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_official_repo_wins_when_previously_aur_package_moves(self):
        official, aur = Mock(), Mock()
        official.is_available.return_value = aur.is_available.return_value = True
        official.contains.return_value = True
        service = InstallService(None, ExecutionContext(False, Mock()), PackageRegistry(),
                                 {"pacman": official, "yay": aur}, inventory=lambda: set())
        with contextlib.redirect_stdout(io.StringIO()):
            service.install_profile(Profile("daily", [Feature("daily", ["vesktop-bin"], [])]))
        official.install.assert_called_once_with(["vesktop-bin"])
        aur.install.assert_not_called()

    def test_dry_run_skips_source_queries_and_state_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / "repo", "tester")
            source, executor = Mock(), Mock()
            service = InstallService(env, ExecutionContext(True, executor), PackageRegistry(), {"pacman": source},
                                     inventory=lambda: set())
            with contextlib.redirect_stdout(io.StringIO()):
                service.install_profile(Profile("test", [Feature("test", ["git"], [])]))
            source.contains.assert_not_called()
            source.is_available.assert_not_called()
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_parser_accepts_multiple_profiles_and_extra_packages(self):
        from dotfiles_api.presentation.cli import build_parser
        args = build_parser().parse_args(["install", "--profile", "daily", "--profile", "dev", "--package", "obs-studio", "--dry-run"])
        self.assertEqual(args.profiles, ["daily", "dev"])
        self.assertEqual(args.packages, ["obs-studio"])

    def test_inventory_reads_names_without_commands(self):
        from dotfiles_api.infrastructure.package_inventory import PackageInventory
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "ALPM_DB_VERSION").write_text("9\n")
            (root / "git-1-1").mkdir()
            (root / "git-1-1/desc").write_text("%NAME%\ngit\n\n%VERSION%\n1-1\n")
            self.assertEqual(PackageInventory(root).names(), {"git"})

    def test_failed_install_preserves_previous_selection(self):
        with tempfile.TemporaryDirectory() as temp:
            env = EnvironmentContext(Path(temp), Path(temp) / "repo", "tester")
            state = env.state_dir / "installation.json"
            state.parent.mkdir(parents=True)
            previous = '{"profiles": ["core"], "packages": ["git"]}'
            state.write_text(previous)
            source = Mock()
            source.is_available.return_value = source.contains.return_value = True
            source.install.side_effect = RuntimeError("installation interrupted")
            service = InstallService(env, ExecutionContext(False, Mock()), PackageRegistry(), {"pacman": source}, inventory=lambda: set())
            with self.assertRaisesRegex(RuntimeError, "Installation failed"), contextlib.redirect_stdout(io.StringIO()):
                service.install_profile(Profile("test", [Feature("test", ["uv"], [])]))
            self.assertEqual(state.read_text(), previous)

    def test_aur_preflight_checks_exact_name_and_reports_invalid_response(self):
        from dotfiles_api.infrastructure.package_sources.yay import YaySource
        source = YaySource(ExecutionContext(False, Mock()))
        for data in ({"results": [{"Name": "different"}]}, ["unexpected response"]):
            stream = io.StringIO(json.dumps(data))
            with patch("dotfiles_api.infrastructure.package_sources.yay.urlopen", return_value=stream):
                if isinstance(data, list):
                    with self.assertRaisesRegex(RuntimeError, "Cannot verify AUR"):
                        source.contains("wanted")
                else:
                    self.assertFalse(source.contains("wanted"))

    def test_setup_rejects_headless_profile_before_installing(self):
        from dotfiles_api.application.services.setup import SetupService
        from dotfiles_api.application.profiles.resolver import DesktopProfileResolver
        env, install = Mock(), Mock()
        service = SetupService(env, ExecutionContext(True, Mock()), install, Mock(), Mock(), Mock(), Mock(), Mock(),
                               profile_resolver=DesktopProfileResolver(lambda: []), selected_profiles=["core"])
        with self.assertRaisesRegex(ValueError, "install --profile"):
            with patch("os.geteuid", return_value=1000):
                service.run_setup()
        install.install_profile.assert_not_called()
