import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from dotfiles_api.application.profiles.software import SoftwareProfileResolver
from dotfiles_api.application.services.install import InstallService
from dotfiles_api.application.registry import PackageRegistry
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.models.feature import Feature
from dotfiles_api.domain.models.profile import Profile
from dotfiles_api.infrastructure.package_inventory import PackageInventory
from dotfiles_api.infrastructure.package_sources.yay import YaySource


class ProfilesRemediationTests(unittest.TestCase):
    def test_legacy_resolved_packages_do_not_become_permanent_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = EnvironmentContext(Path(tmp), Path(tmp) / "repo", "tester")
            path = env.state_dir / "installation.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"version": 1, "profiles": ["core"], "packages": ["obsolete", "git"], "optional_packages": ["user-choice"]}))
            source = Mock()
            source.is_available.return_value = source.contains.return_value = True
            service = InstallService(env, ExecutionContext(False, Mock()), PackageRegistry(), {"pacman": source}, inventory=lambda: {"git"})
            profile = Profile("core", [Feature("core", ["git"], [])], ("core",), (), ("core",))
            with contextlib.redirect_stdout(io.StringIO()):
                service.install_profile(profile)
            state = json.loads(path.read_text())
            self.assertEqual(state["version"], 2)
            self.assertEqual(state["requested_profiles"], ["core"])
            self.assertEqual(state["explicit_packages"], ["user-choice"])
            self.assertNotIn("obsolete", state["packages"])
            self.assertNotIn("obsolete", state["explicit_packages"])

    def test_explicit_package_without_profile_does_not_resolve_desktop(self):
        profile = SoftwareProfileResolver().resolve([], ["spotify"])
        self.assertEqual(profile.get_packages(), ["spotify"])
        self.assertEqual(profile.selected_profiles, ())
        self.assertEqual(profile.requested_profiles, ())

    def test_invalid_and_missing_inventory_do_not_mean_empty_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "missing"
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                PackageInventory(root).names()
            (root / "bad-1").mkdir(parents=True)
            (root / "ALPM_DB_VERSION").write_text("9\n")
            with self.assertRaisesRegex(RuntimeError, "corrupt"):
                PackageInventory(root).names()
            (root / "bad-1/desc").write_text("%NAME%\n\n")
            with self.assertRaisesRegex(RuntimeError, "corrupt"):
                PackageInventory(root).names()

    def test_aur_timeout_network_api_and_missing_are_distinct(self):
        source = YaySource(ExecutionContext(False, Mock()))
        with patch("dotfiles_api.infrastructure.package_sources.yay.urlopen", side_effect=URLError(TimeoutError())) as call:
            with self.assertRaisesRegex(RuntimeError, "timeout"):
                source.contains("x")
            self.assertEqual(call.call_count, 2)
        with patch("dotfiles_api.infrastructure.package_sources.yay.urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(RuntimeError, "network unavailable"):
                source.contains("x")
        with patch("dotfiles_api.infrastructure.package_sources.yay.urlopen", side_effect=HTTPError("", 503, "failed", None, None)):
            with self.assertRaisesRegex(RuntimeError, "HTTP error 503"):
                source.contains("x")
        with patch("dotfiles_api.infrastructure.package_sources.yay.urlopen", return_value=io.StringIO('{"results": []}')):
            self.assertFalse(source.contains("x"))

    def test_setup_tty_does_not_prompt_without_interactive_option(self):
        from dotfiles_api.application.services.setup import SetupService
        from dotfiles_api.application.profiles.resolver import DesktopProfileResolver
        selector = Mock()
        env = Mock()
        svc = SetupService(env, ExecutionContext(False, Mock()), Mock(), Mock(), Mock(), Mock(), Mock(), Mock(),
                           optional_package_selector=selector, profile_resolver=DesktopProfileResolver(lambda: []))
        with patch("sys.stdin.isatty", return_value=True):
            svc.run_setup()
        selector.select.assert_not_called()

    def test_setup_failure_keeps_installed_packages_but_records_configuration_failure(self):
        from dotfiles_api.application.services.setup import SetupService
        from dotfiles_api.application.profiles.resolver import DesktopProfileResolver
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = EnvironmentContext(home, home / "repo", "tester")
            source = Mock()
            source.is_available.return_value = source.contains.return_value = True
            install = InstallService(env, ExecutionContext(False, Mock()), PackageRegistry(),
                                     {"pacman": source, "yay": source}, inventory=lambda: set())
            linker = Mock()
            linker.link.side_effect = OSError("stow failed")
            service = SetupService(env, ExecutionContext(False, Mock()), install, linker, Mock(), Mock(), Mock(), Mock(),
                                   profile_resolver=DesktopProfileResolver(lambda: []))
            with contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(OSError, "stow failed"):
                    service.run_setup()
            state = json.loads((env.state_dir / "installation.json").read_text())
            self.assertEqual(state["package_status"], "complete")
            self.assertEqual(state["desktop_configuration_status"], "failed")
            self.assertEqual(state["session_status"], "not_checked")
