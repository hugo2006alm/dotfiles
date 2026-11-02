import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.facade import DotfilesFacade
from dotfiles_api.application.profiles.desktop import build_desktop_profile
from dotfiles_api.application.services.services import ServicesSetupService
from dotfiles_api.application.services.user import UserSetupService
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult

ROOT = Path(__file__).resolve().parents[2]


class TestBootstrapSafety(unittest.TestCase):
    def test_facade_preserves_resolved_desktop_profile(self):
        profile = build_desktop_profile(optional_packages=["obs-studio"], graphics_packages=["vulkan-intel"])
        install = Mock()
        facade = DotfilesFacade(Mock(), Mock(), install, Mock(), Mock(), Mock())
        facade.apply_profile(profile)
        self.assertIs(install.install_profile.call_args.args[0], profile)

    def test_apply_all_preserves_resolved_desktop_profile(self):
        profile = build_desktop_profile(graphics_packages=["vulkan-radeon"])
        install = Mock()
        DotfilesFacade(Mock(), Mock(), install, Mock(), Mock(), Mock()).apply_all(profile, "shade-raid")
        self.assertIs(install.install_profile.call_args.args[0], profile)

    def test_default_services_do_not_enable_ssh_server(self):
        executor = Mock()
        executor.execute.return_value = CommandResult("", "", 0)
        ServicesSetupService(ExecutionContext(False, executor), Mock()).setup_services()
        self.assertFalse(any("sshd" in call.args[0] for call in executor.execute.call_args_list))

    def test_user_setup_preserves_bash_bookmarks_and_git_preferences(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            originals = {".bashrc": "my shell", ".bash_profile": "my profile",
                         ".bash_history": "my history", ".bash_logout": "my logout",
                         ".config/gtk-3.0/bookmarks": "file:///personal Personal\n"}
            for name, content in originals.items():
                path = home / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            executor = Mock()
            executor.execute.return_value = CommandResult("already-configured", "", 0)
            env = EnvironmentContext(home, home / "dotfiles", "tester")
            UserSetupService(ExecutionContext(False, executor), env).setup_user()
            for name, content in originals.items():
                self.assertTrue((home / name).exists(), name)
                self.assertEqual((home / name).read_text(), content)
            for call in executor.execute.call_args_list:
                self.assertNotIn("mirrorlist", " ".join(call.args[0]))
                self.assertNotEqual(call.args[0], ["git", "config", "--global", "core.pager", "delta"])

    def test_bootstrap_dry_run_and_help_do_not_need_terminal_or_modify_home(self):
        with tempfile.TemporaryDirectory() as temp:
            for args in (["--dry-run", "--github", "--ssh-server"], ["--help"]):
                result = subprocess.run(["bash", str(ROOT / ".config/install/install.sh"), *args],
                                        env={**os.environ, "HOME": temp}, stdin=subprocess.DEVNULL,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(list(Path(temp).iterdir()), [])

    def test_cli_installer_preserves_existing_executable(self):
        installer = ROOT / "scripts/install-cli.sh"
        self.assertTrue(installer.exists(), "Need an isolated CLI installer")
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            command = home / ".local/bin/dotfiles"
            command.parent.mkdir(parents=True)
            command.write_text("personal executable")
            result = subprocess.run(["bash", str(installer)], env={**os.environ, "HOME": temp,
                                    "XDG_DATA_HOME": str(home / ".local/share")},
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("existing", result.stderr.lower())
            self.assertEqual(command.read_text(), "personal executable")
            self.assertFalse((home / ".local/share").exists())
