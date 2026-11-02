import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from dotfiles_api.application.services.services import ServicesSetupService
from dotfiles_api.context.environment import EnvironmentContext
from dotfiles_api.context.execution import ExecutionContext
from dotfiles_api.domain.contracts import CommandResult
from dotfiles_api.infrastructure.reloadables.regreet import ReGreetReloadable


class TestLoginSecurity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.env = EnvironmentContext(self.home, self.home / "dotfiles", "tester")
        self.executor = Mock()
        self.executor.execute.return_value = CommandResult("", "", 0)
        self.ctx = ExecutionContext(False, self.executor)

    def test_normal_setup_does_not_change_login_or_sudoers(self):
        ServicesSetupService(self.ctx, self.env).setup_services()
        for call in self.executor.execute.call_args_list:
            command = " ".join(call.args[0])
            self.assertNotIn("greetd", command)
            self.assertNotIn("sudoers", command)

    def test_theme_reload_never_requests_privileges(self):
        ReGreetReloadable(self.ctx, self.env).reload()
        self.executor.execute.assert_not_called()

    def test_wallpaper_never_writes_login_background_even_if_old_permissions_allow_it(self):
        from dotfiles_api.infrastructure.actions.wallpaper import WallpaperAction

        wallpapers = self.home / "wallpapers/shade-raid"
        wallpapers.mkdir(parents=True)
        (wallpapers / "image.jpg").write_bytes(b"image")
        exists = Path.exists
        with patch("os.access", return_value=True), patch("shutil.which", return_value="/usr/bin/convert"), \
                patch.object(Path, "exists", lambda path: str(path).startswith("/etc/greetd") or exists(path)):
            WallpaperAction(self.ctx, self.env).execute([])
        for call in self.executor.execute.call_args_list:
            self.assertNotIn("/etc/greetd", " ".join(call.args[0]))

    def test_login_requires_interactive_session_before_any_command(self):
        from dotfiles_api.application.services.login import LoginSetupService

        with patch("sys.stdin.isatty", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "interactive"):
                LoginSetupService(self.ctx, self.env).apply()
        self.executor.execute.assert_not_called()

    def test_login_validates_all_inputs_before_privileged_changes(self):
        from dotfiles_api.application.services.login import LoginSetupService

        source = self.home / ".config/greetd"
        source.mkdir(parents=True)
        (source / "regreet.toml").write_text("invalid = [")
        (source / "regreet.css").write_text("window {}")
        (source / "hyprland-greet.conf").write_text("exec-once = regreet")
        with patch("sys.stdin.isatty", return_value=True):
            with self.assertRaises(ValueError):
                LoginSetupService(self.ctx, self.env).apply()
        self.executor.execute.assert_not_called()

    def test_login_uses_private_staging_root_ownership_and_recoverable_backup(self):
        from dotfiles_api.application.services.login import LoginSetupService

        source = self.home / ".config/greetd"
        source.mkdir(parents=True)
        for name, content in {"regreet.toml": "[GTK]\napplication_prefer_dark_theme = true\n",
                              "regreet.css": "window {}",
                              "hyprland-greet.conf": "exec-once = regreet"}.items():
            (source / name).write_text(content)
        staged_modes = []

        def record(args, cwd=None):
            if args[:2] == ["sudo", "install"] and "-T" in args:
                staged_modes.append(Path(args[-2]).stat().st_mode & 0o777)
            return CommandResult("", "", 0)

        self.executor.execute.side_effect = record
        with patch("sys.stdin.isatty", return_value=True):
            backup = LoginSetupService(self.ctx, self.env).apply()
        commands = [call.args[0] for call in self.executor.execute.call_args_list]
        self.assertTrue(str(backup).startswith("/var/backups/shade-raid/"))
        self.assertTrue(staged_modes)
        self.assertEqual(set(staged_modes), {0o600})
        for command in commands:
            self.assertNotIn("666", command)
            if command[:2] == ["sudo", "install"]:
                self.assertIn("root", command)
        self.assertTrue(any("cp -a" in " ".join(command) for command in commands))
        self.assertFalse(any("NOPASSWD" in " ".join(command) for command in commands))


if __name__ == "__main__":
    unittest.main()
